"""Native Manager proposals retain the historical code-update path and gate."""
import ast
import hashlib
import re
from pathlib import Path
from roborsi.agents.safety.gt_firewall import GT_PATTERNS

def attach_failure_source(proposal, repo):
    """Attach current public implementation to a Reviewer's named tool fault.

    The diagnosis remains a hypothesis. Never replace a submitted candidate,
    its source, task identity, or existing validation contract.
    """
    q = dict(proposal)
    if q.get('kind') != 'failure_hypothesis' or q.get('native_source'):
        return q
    root = Path(repo).resolve()
    match = re.match(r'^\[TOOL_BUG ([a-z][a-z0-9_]{0,47}) \d+/\d+\]',
                     str(q.get('root_cause') or ''))
    name = match[1] if match else None
    if name is None:
        # Otherwise use the first existing skill the diagnosis names, so the
        # Manager can judge and revise the skill it blames.
        text = ' '.join(str(q.get(k) or '') for k in ('root_cause', 'next_action', 'rationale'))
        for word in re.findall(r'\b[a-z][a-z0-9_]{2,47}\b', text):
            if (root / 'roborsi/embodied/skills/base' / word / 'libero/policy.py').is_file():
                name = word
                break
    if name is None:
        return q
    source = root / 'roborsi/embodied/skills/base' / name / 'libero/policy.py'
    if not source.is_file() or not source.resolve().is_relative_to(root):
        return q
    document = source.with_name('SKILL.md')
    if not document.is_file() or not document.resolve().is_relative_to(root):
        return q
    content = source.read_text(encoding='utf-8')
    q.update(development_mode='native', native_source=content,
             native_source_path=str(source.relative_to(root)),
             native_source_sha256=hashlib.sha256(content.encode('utf-8')).hexdigest())
    q.setdefault('skill_md', document.read_text(encoding='utf-8'))
    return q


def unified_review_system(proposal, base_system, harness_contract):
    """One review path for lessons, plans, native changes and compounds."""
    system = request_system(proposal, base_system) + '\n' + harness_contract
    if proposal.get('kind') == 'failure_hypothesis':
        system += '''
This is a Reviewer diagnosis, not an already-authored repair. A TOOL_BUG label
is a hypothesis, not proof of an implementation defect. Evaluate the preserved
public execution evidence independently. Any native_source supplied here is the
current skill implementation, not a proposed replacement. You may diagnose a
planning, perception, parameter, physical execution or implementation issue;
do not force every failure into a code-bug explanation. You may author a useful
same-name native update or a new skill. Code you author is queued for separate
Manager review and the existing simulator publication gate. Keep lesson approval
separate from the decision to develop code. Do not demand that unwritten code
already have a successful simulation result.
'''
    return system


def request_system(proposal, base_system):
    if proposal.get('kind') != 'code_revision_request':
        return base_system
    from roborsi.agents.roles.manager.patch_review import patch_prompt
    return base_system + '''

CURRENT STAGE: MANAGER AUTHORS A CANDIDATE; THIS IS NOT CANDIDATE APPROVAL.
native_source and skill_md are the CURRENT implementation and its current
documentation, supplied for editing. They are not an already-repaired candidate.
revision_request asks YOU, the Manager, to produce code_proposal with a complete
changed native implementation and the complete declared functional harness.
Absence of an edit or harness in the CURRENT implementation is an authoring task,
not a reason to reject an allegedly submitted unchanged candidate. Likewise,
the first simulator trial is how an unvalidated repair hypothesis is tested;
do not require a successful trial that has not yet been authorized or run.
Assess the public failure evidence and causal uncertainty. If it supports a
concrete testable repair, AUTHOR it without claiming it works. Preserve every
declared task, seed and pass criterion, native interfaces and physical interlocks.
If evidence does not support any concrete repair, explain precisely what is
missing; do not invent evidence or force a candidate.
Use decision=defer for the design request when returning a new code_proposal:
no existing candidate is being approved here. Your code is queued for a later,
separate actual Manager review, then the unchanged simulator gate, then publication.
No separate Developer exists, and no code is self-approved in this response.
''' + patch_prompt(proposal)

# Accessors that reveal object identities, task goals or the success predicate.
# Robot proprioception, robot geometry and camera calibration stay available.
_FORBIDDEN_STATE = {
    "obj_of_interest", "objects_dict", "object_sites_dict", "fixtures_dict",
    "get_object", "obj_body_id", "obj_geom_id", "parsed_problem", "goal_state",
    "_check_success", "check_success", "_eval_predicate", "bddl_file_name",
}
_FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__", "globals", "locals",
                    "vars", "breakpoint"}
_REFLECTIVE_CALLS = {"getattr", "setattr", "delattr", "hasattr"}
_FORBIDDEN_MODULES = {"subprocess", "socket", "shutil", "ctypes", "multiprocessing",
                      "requests", "urllib", "http", "ftplib", "importlib"}


def _module_string_constants(tree):
    names = set()
    for node in tree.body:
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


def assert_native_candidate(code):
    """Reject native code that reads hidden task state or escapes the skill ABI.

    Native skills may use robot proprioception, robot geometry, camera
    calibration and public sensors. Everything else still requires Manager
    review; this check is the mechanical floor that review cannot waive.
    """
    tree = ast.parse(code)
    constants = _module_string_constants(tree)
    for n in ast.walk(tree):
        token = n.id if isinstance(n, ast.Name) else n.attr if isinstance(n, ast.Attribute) else None
        if token and (token in _FORBIDDEN_STATE or any(p.search(token) for p in GT_PATTERNS)):
            raise ValueError('Native proposal reads forbidden task state: ' + token)
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ""]
            for name in names:
                if name.split(".")[0] in _FORBIDDEN_MODULES:
                    raise ValueError('Native proposal imports a forbidden module: ' + name)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            if n.func.id in _FORBIDDEN_CALLS:
                raise ValueError('Native proposal uses dynamic execution: ' + n.func.id)
            if n.func.id in _REFLECTIVE_CALLS:
                name_arg = n.args[1] if len(n.args) >= 2 else None
                if isinstance(name_arg, ast.Constant) and isinstance(name_arg.value, str):
                    if name_arg.value in _FORBIDDEN_STATE or any(p.search(name_arg.value) for p in GT_PATTERNS):
                        raise ValueError('Native proposal names forbidden task state: ' + name_arg.value)
                elif not (isinstance(name_arg, ast.Name) and name_arg.id in constants):
                    raise ValueError('Native proposal uses a computed attribute name in ' + n.func.id)
    return tree
