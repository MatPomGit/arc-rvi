"""Analytic fixture references for conservative URDF primitive envelopes."""

from __future__ import annotations

from hashlib import sha256
from math import hypot, sqrt
from pathlib import Path
import tempfile
import unittest

from rvi.robot_model import inspect_urdf
from rvi.collision import inspect_collision_proxies


MODEL = """<robot name="synthetic_collision_references">
<link name="base">
  <collision><geometry><box size="2 2 2"/></geometry></collision>
</link>
<link name="arm">
  <collision><origin xyz="1 0 0" rpy="0 0 1.5707963267948966"/>
    <geometry><cylinder radius="0.2" length="2"/></geometry>
  </collision>
</link>
<link name="camera">
  <collision><geometry><sphere radius="0.3"/></geometry></collision>
</link>
<joint name="yaw" type="revolute">
  <parent link="base"/><child link="arm"/>
  <axis xyz="0 0 1"/><limit lower="-1" upper="1"/>
</joint>
<joint name="mount" type="fixed">
  <parent link="arm"/><child link="camera"/><origin xyz="1 0 0"/>
</joint>
</robot>"""


def fixture() -> dict:
    return {
        "schema_version": "1.0.0", "clearance_margin_m": 0.0,
        "spheres": [
            {"id": "base_sphere", "link": "base",
             "center_local_m": [0, 0, 0], "radius_m": 1.9},
            {"id": "arm_sphere", "link": "arm",
             "center_local_m": [1, 0, 0], "radius_m": 1.1},
            {"id": "camera_sphere", "link": "camera",
             "center_local_m": [0, 0, 0], "radius_m": 0.4},
        ],
        "boxes": [
            {"id": "distant", "min_xyz_m": [20, 20, 20],
             "max_xyz_m": [21, 21, 21]},
        ],
        "self_pairs": [],
    }


class UrdfPrimitiveEnvelopeAuditTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.path = Path(self.workspace.name) / "synthetic.urdf"

    def check(self, xml: str = MODEL, declared: dict | None = None):
        raw = xml.encode("utf-8")
        self.path.write_bytes(raw)
        fk = inspect_urdf(
            self.path, sha256(raw).hexdigest(),
            joint_positions={"yaw": 0.0})["configured_joint_pose"]
        return fk, inspect_collision_proxies(fk, declared or fixture())

    def test_conservative_box_cylinder_sphere_reference_bounds(self):
        fk, report = self.check()
        metadata = fk["urdf_collision_geometry"]
        base = metadata["by_link"]["base"][0]
        arm = metadata["by_link"]["arm"][0]
        camera = metadata["by_link"]["camera"][0]
        self.assertAlmostEqual(base["bounding_sphere_radius_m"], sqrt(3))
        self.assertAlmostEqual(arm["bounding_sphere_radius_m"], hypot(0.2, 1))
        self.assertEqual(arm["bounding_sphere_centre_local_m"], [1, 0, 0])
        self.assertEqual(camera["bounding_sphere_radius_m"], 0.3)
        self.assertTrue(all(e["status"] == "analytic_primitive_bound"
                            for e in (base, arm, camera)))
        audit = report["urdf_primitive_envelope_audit"]
        self.assertEqual(audit["primitive_collision_elements"], 3)
        self.assertEqual(audit["enclosed_primitive_bounds"], 3)
        self.assertEqual(audit["not_demonstrated_or_unknown"], 0)
        self.assertEqual(audit["links_without_urdf_collision_reference"], [])
        self.assertEqual(audit["status"],
                         "declared_urdf_primitives_enclosed_unverified_robot")
        self.assertEqual(audit["actual_link_collision_volume_validation"],
                         "not_performed")
        self.assertEqual(report["full_body_collision_validation"], "not_performed")
        self.assertEqual(report["status"], "no_proxy_overlap_unverified")
        self.assertFalse(audit["mesh_files_loaded"])

    def test_too_small_proxy_is_not_treated_as_enclosing_reference(self):
        declared = fixture()
        declared["spheres"][1]["radius_m"] = 0.6
        _, report = self.check(declared=declared)
        audit = report["urdf_primitive_envelope_audit"]
        self.assertEqual(audit["enclosed_primitive_bounds"], 2)
        self.assertEqual(audit["not_demonstrated_or_unknown"], 1)
        self.assertEqual(audit["primitive_checks"][1]["status"],
                         "primitive_enclosure_not_demonstrated")
        self.assertEqual(audit["status"],
                         "incomplete_or_unverified_reference_coverage")

    def test_displaced_proxy_and_missing_declared_link(self):
        declared = fixture()
        declared["spheres"][1]["center_local_m"] = [0, 0, 0]
        declared["spheres"][1]["radius_m"] = 1.5
        _, report = self.check(declared=declared)
        # Tip geometry is centred 1 m along arm: 1 + sqrt(1.04) > 1.5.
        self.assertEqual(report["urdf_primitive_envelope_audit"]
                         ["primitive_checks"][1]["status"],
                         "primitive_enclosure_not_demonstrated")
        declared["spheres"] = [s for s in declared["spheres"]
                               if s["link"] != "camera"]
        _, report = self.check(declared=declared)
        self.assertEqual(report["urdf_primitive_envelope_audit"]
                         ["primitive_checks"][2]["status"],
                         "missing_declared_link_proxy")

    def test_external_mesh_is_unknown_and_is_never_loaded(self):
        xml = MODEL.replace(
            '<sphere radius="0.3"/>',
            '<mesh filename="package://not-available/mesh.stl" scale="1 1 1"/>')
        fk, report = self.check(xml)
        item = fk["urdf_collision_geometry"]["by_link"]["camera"][0]
        self.assertEqual(item["status"], "unverified_geometry")
        self.assertEqual(item["primitive_kind"], "mesh")
        self.assertIsNone(item["bounding_sphere_radius_m"])
        audit = report["urdf_primitive_envelope_audit"]
        self.assertEqual(audit["primitive_checks"][2]["status"],
                         "unverified_reference_geometry")
        self.assertEqual(audit["not_demonstrated_or_unknown"], 1)
        self.assertFalse(audit["mesh_files_loaded"])
        self.assertEqual(audit["status"],
                         "incomplete_or_unverified_reference_coverage")

    def test_invalid_nan_zero_and_overflow_geometry_remain_unknown(self):
        for bad in ('nan', '-2', '0', '1e309'):
            with self.subTest(bad=bad):
                xml = MODEL.replace('<sphere radius="0.3"/>',
                                    f'<sphere radius="{bad}"/>')
                _, report = self.check(xml)
                check = report["urdf_primitive_envelope_audit"]["primitive_checks"][2]
                self.assertEqual(check["status"], "unverified_reference_geometry")
        xml = MODEL.replace('<sphere radius="0.3"/>',
                            '<box size="1 1 1e309"/>')
        _, report = self.check(xml)
        self.assertEqual(report["urdf_primitive_envelope_audit"]
                         ["not_demonstrated_or_unknown"], 1)

    def test_absent_collision_elements_are_not_mistaken_for_full_coverage(self):
        xml = MODEL.replace(
            '<collision><geometry><sphere radius="0.3"/></geometry></collision>', '')
        _, report = self.check(xml)
        audit = report["urdf_primitive_envelope_audit"]
        self.assertEqual(audit["links_without_urdf_collision_reference"],
                         ["camera"])
        self.assertEqual(audit["primitive_collision_elements"], 2)
        self.assertEqual(audit["status"],
                         "incomplete_or_unverified_reference_coverage")

    def test_multiple_collision_elements_must_each_be_enclosed(self):
        xml = MODEL.replace(
            '<collision><geometry><sphere radius="0.3"/></geometry></collision>',
            '<collision><geometry><sphere radius="0.3"/></geometry></collision>'
            '<collision><origin xyz="2 0 0"/>'
            '<geometry><sphere radius="0.3"/></geometry></collision>')
        _, report = self.check(xml)
        checks = report["urdf_primitive_envelope_audit"]["primitive_checks"]
        self.assertEqual(len(checks), 4)
        self.assertEqual(checks[2]["status"],
                         "circumsphere_enclosed_by_declared_proxy")
        self.assertEqual(checks[3]["status"],
                         "primitive_enclosure_not_demonstrated")

    def test_wrong_source_hash_still_rejected_and_legacy_pose_is_unknown(self):
        self.path.write_text(MODEL)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            inspect_urdf(self.path, "0" * 64, joint_positions={"yaw": 0})
        fk, _ = self.check()
        del fk["urdf_collision_geometry"]
        audit = inspect_collision_proxies(fk, fixture())["urdf_primitive_envelope_audit"]
        self.assertEqual(audit["status"], "urdf_collision_reference_unavailable")
        self.assertEqual(audit["actual_link_collision_volume_validation"],
                         "not_performed")


if __name__ == "__main__":
    unittest.main()
