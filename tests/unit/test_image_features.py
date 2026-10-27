"""Checks for synthetic image pixels, intentionally not camera validation."""
import unittest

from rvi.image_features import (
    pixel_distance, render_patch, texture_templates, validate_pixels,
)


class ImageFeatureTests(unittest.TestCase):
    def test_exact_similarity_factor(self):
        similar = texture_templates(123, "family_a", "similar")
        distinct = texture_templates(123, "family_a", "distinct")
        self.assertEqual(similar["target"], distinct["target"])
        self.assertEqual(sum(a != b for a, b in zip(
            similar["target"], similar["distractor"])), 4)
        self.assertEqual(sum(a != b for a, b in zip(
            distinct["target"], distinct["distractor"])), 40)
        self.assertGreater(pixel_distance(distinct["target"], distinct["distractor"]),
                           pixel_distance(similar["target"], similar["distractor"]))
        self.assertEqual(pixel_distance(distinct["target"], distinct["target"]), 0)

    def test_frame_noise_replay_and_shared_session_bias(self):
        template = texture_templates(1, "family_b", "distinct")["target"]
        first = render_patch(template, 1, "session_a", 0, "target")
        self.assertEqual(first, render_patch(template, 1, "session_a", 0, "target"))
        self.assertNotEqual(first, render_patch(template, 1, "session_a", 1, "target"))
        self.assertNotEqual(first, render_patch(template, 1, "session_b", 0, "target"))
        self.assertEqual(len(first), 64)
        self.assertTrue(all(type(px) is int and 0 <= px <= 255 for px in first))

    def test_invalid_pixel_values_rejected(self):
        valid = [128] * 64
        for bad in (valid[:-1], [256] + valid[1:],
                    [True] + valid[1:], [-1] + valid[1:],
                    [float("nan")] + valid[1:], "0" * 64):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_pixels(bad)
        with self.assertRaises(ValueError):
            pixel_distance(valid, [0])
        with self.assertRaises(ValueError):
            render_patch(valid, 3, "session", -1, "target")
        with self.assertRaises(ValueError):
            texture_templates(3, "family", "unknown")


if __name__ == "__main__":
    unittest.main()
