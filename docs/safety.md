# Physical experiment safety

No real robot control exists in the initial repository. Before enabling one,
document emergency stop tests, workspace boundaries, protected distances,
human supervisor, safe speeds, collision handling, loss-of-localization
behavior, loss-of-network behavior and termination criteria.

A motion adapter must fail closed when safety prerequisites are absent.
Physical tests require site authorization and verified hardware procedures.
Never interpret success on a static synthetic fixture as a safety guarantee.

Unitree G1 EDU is the designated **future** test platform, not an authorized
motion target. Before any test on that hardware, verify its exact variant,
manufacturer safety/operating guidance, emergency stop, manual enable, fall
zone, speed/force limits, supervisor and independently tested motion disable.
Record hardware, firmware and safety-check revisions per session. The current
`adapter: not_configured` must remain unchanged until these gates pass.

The user-supplied G1 EDU teaching manual v1.8 (sections 3, 7–10, 14)
describes a useful staged preflight: **M0** supervised workspace and
manual emergency takeover; **M1** verified communication; **M2**
read-only joint/IMU telemetry with synchronized, complete logs. Treat
these as prerequisites, **not permission**, for an independently reviewed
motion-stage protocol. During hardware work, assign a distinct operator
to pilot/emergency stop and another to diagnostics; avoid competing
SDK/ROS 2 controllers. Check optional dexterous-hand cabling and
posture restrictions before any movement.

Do not place default passwords, device-specific IPs or access instructions
from training materials in this public repository. Manufacturer safety
guidance and the actual hardware configuration take precedence over
unverified teaching examples.
