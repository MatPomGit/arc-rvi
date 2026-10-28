# Physical experiment safety

A non-actuating initial inventory can be requested through
`scripts/inspect_robot_ssh.py` via SSH from an authorized developer
computer. It does not publish to DDS command channels, start a motor,
change services, or modify robot configuration. The optional DDS read
still requires permission to access the network and is no substitute
for on-site safety checks. Store the resulting JSON locally.

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

## Difficult-terrain humanoid operating gate (prospective, 2026-10-28)

A humanoid can lose balance even when its **planned camera viewpoint**
and horizontal path are geometrically clear. In a cluttered or damaged
environment, **fall exposure** covers more than the nominal foot
footprint. The following are review gates, **not** authorization to
drive or train on hazardous terrain.

- **M0/M1/M2 first:** identify and verify the specific G1 EDU variant,
  available safety-rated stop and recovery procedure, actuator/sensor
  state, measured camera transforms, operator roles and the actual site.
  No autonomous motion is permitted by this document.
- **Site hazards:** survey slopes and steps, foot-support continuity,
  uncertain/slippery/loose material, cables, falling objects, low beams,
  narrowing passages, unobserved edges and human access. Record an
  independently approved no-go region and physical fall/retreat zone;
  assume an observed flat patch can have **unknown traction**.
- **Staged evidence:** static offline modelling → independently checked
  articulated/contact simulations → non-moving sensing/calibration
  under supervision → independently approved, supported low-risk
  experiments → only subsequently, if authorized, graded terrain.
  **Do not** place this robot on rubble, gaps or inclined/slippery
  obstacles as an informal verification step.
- **Monitored stop/abort conditions:** uncertain support or foothold,
  inability to verify full-body clearance or a safe retreat, slip or
  unexpected contact, substantial pose/sensor disagreement, unstable
  motion, people entering exclusion zone, supervisor command and
  communications faults. An abort means no subsequent attempted
  acquisition is credited; record the cause and partial data.
- **Fallback and evidence:** stop/hold/retreat mechanisms must be
  designed and physically validated separately, including loss of
  communications and failure of localization. Never assume a
  machine-learning locomotion policy, lab harness or preflight
  collision check provides certified fall protection. Preserve
  near-misses, operator takeovers, failed missions and missing images.

**No numerical incline, friction, obstacle-size or fall-margin limit
can be inferred for the actual delivered G1 EDU** from third-party
G1 locomotion publications, vendor marketing or the current software.
A qualified site risk assessment must set and verify bounds before
each approved physical stage. Other papers' robot platforms, control
policies and measured terrain successes do not establish G1 EDU
inspection-system safety.

## Photographic laboratory walkthrough (2026-10-27)

Three user-supplied still photographs show an upright, humanoid-shaped robot
identified by the user as G1 EDU, with its feet on a tiled floor. Visible
straps near the body and a wheeled overhead/adjacent structure **may** be part
of a support arrangement; the pictures cannot establish attachment,
load-rating, correct fit, fall arrest or active supervision. Nearby chairs,
bags and floor-level cables warrant a **site-specific** inspection for
trip hazards, reachable obstructions and the fall/motion envelope.

**No safety clearance is established by the photographs.** Motion state,
power, physical robot revision, emergency-stop availability, pilot takeover,
controller exclusivity, support load path and operator authorization cannot
be verified from these images. Before work beyond read-only inspection,
perform the documented M0/M1/M2 checks on site, log results, mark and clear
an approved operating perimeter and verify the support manufacturer's
instructions with qualified personnel. Keep photos outside public Git; do
not count them as a physical experiment or safety test.

Do not place default passwords, device-specific IPs or access instructions
from training materials in this public repository. Manufacturer safety
guidance and the actual hardware configuration take precedence over
unverified teaching examples.
