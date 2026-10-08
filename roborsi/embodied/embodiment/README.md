# Connecting a Real Robot

RoboRSI's roles never talk to a simulator or robot directly. The Engineer
calls **skills**; skills act through an **environment** (`Env`) supplied by a
**backend**. To connect your robot you implement those two layers and a set of
base skills for it. Planner, Reviewer, Manager, the task wiki and the
evolution loop then work unchanged.

```
Planner / Reviewer / Manager            (unchanged)
        │
Engineer ──► base & compound skills     skills/base/<skill>/<ns>/   ← you add <ns>
        │
      Env  (reset / take_snapshot / close)                         ← you implement
        │
 your robot SDK, cameras, grippers      embodiment/ (optional)
```

## 1. Implement `Env` and `Backend`

The contract is in `roborsi/embodied/agent_loop/env.py`.

```python
# my_robot/backend.py
from roborsi.embodied.agent_loop.env import Backend, Env, Observation

class MyRobotEnv(Env):
    backend_name = "my-robot"

    def __init__(self, task: str):
        self.task = task
        self.instruction = ""          # filled by reset(); read by the Planner
        self.robot = MyRobotSDK.connect()
        self.cameras = {"head": HeadCamera(), "wrist": WristCamera()}

    def reset(self, seed: int) -> Observation:
        # A real robot cannot reseed a scene. Move to a safe home pose and
        # read the instruction for this episode (operator, task file, ...).
        self.robot.go_home()
        self.instruction = load_instruction(self.task)
        return self.take_snapshot()

    def take_snapshot(self) -> Observation:
        return Observation(
            images={name: cam.read_rgb() for name, cam in self.cameras.items()},
            state=self.robot.joint_positions(),
            extras={"instruction": self.instruction},
        )

    def check_success(self):
        return None                    # no ground-truth predicate on a real robot

    def close(self) -> None:
        self.robot.go_home()
        self.robot.disconnect()


class MyRobotBackend(Backend):
    name = "my-robot"

    def list_tasks(self) -> list[str]:
        return ["tidy_table", "load_dishwasher"]

    def make_env(self, task, config=None) -> Env:
        return MyRobotEnv(task)
```

Rules that the rest of the system relies on:

- `Observation.images` holds HWC uint8 RGB arrays keyed by camera name;
  `state` is proprioception. Put only what a camera-and-encoder robot really
  measures here. Object poses or task state from any privileged source must
  not appear in observations or tool results.
- `check_success()` returns `None` on a real robot. The episode outcome then
  comes from the Engineer's completion claim as checked by the Reviewer from
  the camera views, and you can confirm it by hand.
- `reset()` must leave the robot in a safe state; `close()` is always called,
  also after errors.

## 2. Register the backend and its skill namespace

```python
from roborsi.embodied.agent_loop import register
register("my-robot", lambda: MyRobotBackend())
```

Map the backend to a skill namespace in
`roborsi/embodied/agent_loop/config.py` (`_BACKEND_SKILL_NS`), for example
`"my-robot": "myrobot"`. Several backends can share one namespace when they
drive the same embodiment.

## 3. Write base skills for the namespace

Each Engineer tool is `skills/base/<skill>/<ns>/` with a `SKILL.md`
(the contract the Engineer sees) and a `policy.py`:

```python
# skills/base/gripper/myrobot/policy.py
def dispatch_runtime(state, args):
    want = args.get("state")
    if want not in ("open", "close"):
        return {"ok": False, "reason": "state must be 'open' or 'close'"}, state.env.take_snapshot()
    state.env.robot.set_gripper(closed=(want == "close"))
    width = state.env.robot.gripper_width()
    reached = (width > 0.07) if want == "open" else (width < 0.07)
    return ({"ok": reached, "gripper_width": width,
             "reason": None if reached else "gripper did not reach the requested state"},
            state.env.take_snapshot())
```

Every skill returns `(result_dict, Observation)`. Report failures honestly
(`ok: false` with a reason): the Reviewer and the Manager learn from these
results. A useful starting set, mirroring `skills/base/*/libero/`:

| Kind | Skills |
|---|---|
| Perception | `look`, `find_by_pointing` or `detect_object`, `unproject_pixel` (pixel + depth → 3-D point), `zoom_in` |
| State | `get_arm_pose`, `is_holding`, `read_joint_state` |
| Motion | `move_to_pose`, `move_ee_delta`, `home`, `gripper` |
| Manipulation | `grasp_object`, `place_on_surface`, `place_object_in`, task-specific skills such as `pull_drawer` |

Use the LIBERO implementations as references. Their perception helpers
(`skills/base/_lib/libero/_perception.py`) read depth and camera matrices
through the LIBERO environment; for your robot, expose depth and the camera
intrinsics and extrinsics from your `Env` (for example as methods your skills
call) and adapt those helpers.

## 4. Describe the task

Add an atomic task under `skills/atomic/<task>/SKILL.md` with
`metadata.backends: [my-robot]` and the instruction prompt for the Engineer
(see `skills/atomic/libero_pick_place/SKILL.md`). Then run it:

```bash
roborsi eval <task> --backend my-robot --seeds 3                     # frozen
roborsi eval <task> --backend my-robot --seeds 3 --run-mode evolve   # with evolution
```

## 5. Hardware drivers (optional)

`embodiment/` holds reusable device layers: `arm/` (Flexiv example:
client, session lifecycle, protocol), `hand/` (dexterous hands over Modbus),
`camera/`, `interface/` (serial, CAN, video), `hardware/` (device discovery
and monitoring) and `manifest/` (which device is bound to which slot). You
can call your own SDK from `Env` instead; these modules only help when you
want discovery and binding for several devices.

## 6. Safety and evolution on hardware

- Keep motion limits, workspace bounds and an emergency stop inside your
  `Env` and motion skills, not in prompts.
- The Manager publishes a code change only after a gate passes. On hardware
  the episode-level gate runs real episodes, so supervise it, or run the gate
  in a simulator of the same robot and review the change before it reaches
  the real robot.
- Start in frozen mode to check your skills, then enable evolution.
