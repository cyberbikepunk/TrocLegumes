from apps.farms.utils import haversine_km


class TestHaversineKm:
    def test_same_point_is_zero(self):
        assert haversine_km(48.0, 2.0, 48.0, 2.0) == 0.0

    def test_known_distance_paris_to_lyon(self):
        # Paris (48.8566, 2.3522) to Lyon (45.7640, 4.8357) ≈ 392 km
        dist = haversine_km(48.8566, 2.3522, 45.7640, 4.8357)
        assert 380 < dist < 410

    def test_is_symmetric(self):
        d1 = haversine_km(48.0, 2.0, 43.0, 5.0)
        d2 = haversine_km(43.0, 5.0, 48.0, 2.0)
        assert abs(d1 - d2) < 0.001
