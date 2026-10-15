import unittest

import numpy as np

from nervegear_benchmark import core


class CausalFeaturesTests(unittest.TestCase):
    def setUp(self):
        self.emg = np.arange(32, dtype=float).reshape(16, 2) / 10
        self.time = np.arange(16) / 2000

    def test_trailing_features_are_aligned_and_future_invariant(self):
        ends, features, valid = core.features(self.emg, self.time, 4, 2, 7, 8)
        np.testing.assert_array_equal(ends, [7, 9, 11, 13, 15])
        expected = np.log1p(np.sqrt(np.mean(self.emg[4:8] ** 2, axis=0)))
        np.testing.assert_allclose(features[0], expected)
        changed = self.emg.copy()
        changed[8:] = 10000
        _, future_features, _ = core.features(changed, self.time, 4, 2, 7, 8)
        np.testing.assert_array_equal(features[0], future_features[0])
        self.assertTrue(valid.all())

    def test_gap_and_nonfinite_history_are_excluded_with_recovery(self):
        time = self.time.copy()
        time[6:] += 0.01
        _, _, gap_valid = core.features(self.emg, time, 4, 2, 7, 8)
        np.testing.assert_array_equal(gap_valid, [False, False, False, True, True])
        emg = self.emg.copy()
        emg[4, 0] = np.nan
        _, x, valid = core.features(emg, self.time, 4, 2, 7, 8)
        np.testing.assert_array_equal(valid, [False, False, False, True, True])
        self.assertTrue(np.isfinite(x[valid]).all())

    def test_short_recording_produces_no_windows(self):
        ends, x, valid = core.features(self.emg[:4], self.time[:4], 4, 2, 7, 8)
        self.assertEqual(x.shape, (0, 2))
        self.assertEqual(len(ends), 0)
        self.assertEqual(len(valid), 0)

    def test_reference_mask_is_not_a_rest_label(self):
        y = np.ones((4, 20))
        y[0] = 0
        y[1, 4] = np.nan
        y[2] = 1e-10
        np.testing.assert_array_equal(core.reference_valid(y), [False, False, False, True])


class ModelAndScoreTests(unittest.TestCase):
    def test_training_statistics_and_intercept_are_preserved(self):
        x = np.array([[1, 8], [2, 8], [3, 8]], dtype=float)
        y = 3 * x[:, :1] + 4
        model = core.fit_ridge(x, y, 0.1)
        np.testing.assert_allclose(model.mean, [2, 8])
        np.testing.assert_allclose(model.scale, [np.sqrt(2 / 3), 1])
        before = model.predict(x)
        model.predict(np.array([[100000, -100000]]))
        np.testing.assert_array_equal(model.predict(x), before)
        np.testing.assert_allclose(model.predict(model.mean[None]), [[10]])
        self.assertLess(np.abs(before - y).mean(), 0.1)

    def test_primary_metric_weights_recordings_equally(self):
        records = [
            core.errors(np.zeros((1, 2)), np.ones((1, 2))),
            core.errors(np.zeros((9, 2)), np.full((9, 2), 3.0)),
        ]
        score = core.aggregate(records)
        self.assertEqual(score["macro_mae_rad"], 2)
        self.assertEqual(score["sample_weighted_mae_rad"], 2.8)
        self.assertEqual(score["scored_outputs"], 10)

    def test_empty_or_nonfinite_scores_are_errors(self):
        with self.assertRaisesRegex(ValueError, "scored"):
            core.errors(np.empty((0, 2)), np.empty((0, 2)))
        with self.assertRaisesRegex(ValueError, "finite"):
            core.errors(np.array([[np.nan]]), np.array([[1]]))

    def test_corruptions_are_seeded_and_channel_specific(self):
        x = np.ones((12, 16))
        rms = np.ones(16)
        np.testing.assert_array_equal(core.corrupt(x, "clean", rms, 0), x)
        dropped = core.corrupt(x, "drop_channel_0", rms, 0)
        np.testing.assert_array_equal(dropped[:, 0], 0)
        np.testing.assert_array_equal(dropped[:, 1:], x[:, 1:])
        np.testing.assert_array_equal(core.corrupt(x, "gain_0.5", rms, 0), x * 0.5)
        a = core.corrupt(x, "noise_0.1", rms, 0)
        b = core.corrupt(x, "noise_0.1", rms, 0)
        np.testing.assert_array_equal(a, b)
        self.assertFalse(np.array_equal(a, x))


if __name__ == "__main__":
    unittest.main()
