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
