import unittest

from crosshair_renderer import render_crosshair_bgra, render_crosshair_image


class CrosshairRendererTests(unittest.TestCase):
    def test_renderer_returns_expected_image_and_bytes(self):
        settings = {
            "size": 20,
            "thickness": 2,
            "gap": 4,
            "color": "#00FF00",
            "opacity": 1.0,
            "outline_enabled": True,
            "outline_color": "#000000",
            "outline_width": 1,
            "pixel_perfect": False,
            "center_dot": True,
            "center_dot_size": 3,
            "center_dot_color": "#FF0000",
            "rainbow_mode": False,
            "dynamic_color": False,
        }

        image = render_crosshair_image(settings, size=128)
        data = render_crosshair_bgra(settings, size=128)

        self.assertEqual(image.size, (128, 128))
        self.assertEqual(len(data), 128 * 128 * 4)
        self.assertGreater(max(image.getchannel("A").getdata()), 0)

if __name__ == "__main__":
    unittest.main()
