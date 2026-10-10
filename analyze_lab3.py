"""Reproduce Lab 3 experiments 4 and 5 without filling missing observations.

Dependencies: NumPy. Figures have separate editable LaTeX sources in figures/.
All numerical work uses unrounded input. Reading uncertainties are estimates,
and the fit covariance below is conditional on treating those scales as independent.
"""
from pathlib import Path
import csv
import json
import math
import numpy as np


def maximum_coordinates(count=4):
    """Positive side maxima of sinc(beta)^2, excluding the central maximum."""
    roots = []
    for order in range(1, count+1):
        lo = order*math.pi + 1e-9
        hi = (order+.5)*math.pi - 1e-9
        for _ in range(80):
            mid = (lo+hi)/2
            if math.tan(mid)-mid > 0:
                hi = mid
            else:
                lo = mid
        roots.append((lo+hi)/(2*math.pi))
    return np.array(roots)


def weighted_scale(coordinate, measurements, uncertainties):
    coordinate, measurements, uncertainties = map(np.asarray, (coordinate, measurements, uncertainties))
    precision = np.sum(coordinate**2/uncertainties**2)
    scale = np.sum(coordinate*measurements/uncertainties**2)/precision
    scale_error = precision**-.5
    fitted = scale*coordinate
    residuals = (measurements-fitted)/uncertainties
    return scale, scale_error, fitted, residuals


def write_csv(path, columns, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def fit_summary(coordinate, measurements, uncertainties):
    slope, slope_error, fitted, residuals = weighted_scale(coordinate, measurements, uncertainties)
    degrees_of_freedom = len(measurements)-1
    diagnostic = float(np.sum(residuals**2))
    return {
        'coordinate': list(map(float, coordinate)),
        'measurements_cm': list(map(float, measurements)),
        'reading_scales_cm': list(map(float, uncertainties)),
        'intercept_cm': 0.,
        'slope_cm': float(slope), 'slope_reading_scale_cm': float(slope_error),
        'fitted_spans_cm': fitted.tolist(),
        'normalized_residuals': residuals.tolist(),
        'residual_plot_error_bars': [1.]*len(measurements),
        'weighted_chi_squared_diagnostic': diagnostic,
        'degrees_of_freedom': degrees_of_freedom,
        'reduced_weighted_diagnostic': diagnostic/degrees_of_freedom,
    }


def run_analysis(output_dir=None):
    root = Path(output_dir) if output_dir is not None else Path(__file__).resolve().parent
    data = root/'data'
    data.mkdir(parents=True, exist_ok=True)
    z = maximum_coordinates()
    distances = np.array([1.02, 1.98, 2.97])
    errors = np.array([.05, .1, .05])
    K, uK, fitted, residuals = weighted_scale(z[:3], distances, errors)
    wavelength = 634.6e-9
    L = (81.27-5.00)/100
    w = 2*wavelength*L/(K/100)
    uw = w*uK/K
    thick_span, thick_error = 1.15, .4
    thick_K, thick_uK = thick_span/z[3], thick_error/z[3]
    thick_w = 2*wavelength*L/(thick_K/100)
    thick_uw = thick_w*thick_error/thick_span
    fine_K, fine_uK, fine_fitted, fine_residuals = weighted_scale(
        [1., 2.], [.25, .46], [.05, .05]
    )
    envelope_K, envelope_uK, _, _ = weighted_scale(z[:2], [.8, 1.35], [.1, .05])
    third_prediction = envelope_K*z[2]
    third_u = envelope_uK*z[2]
    discrepancy = (3.12-third_prediction)/math.sqrt(.2**2+third_u**2)
    Q = float(np.sum(residuals**2))
    results = {
        'wire': {
            'maximum_coordinates_beta_over_pi': z.tolist(),
            'recorded_thin_spans_cm': distances.tolist(),
            'reading_scales_cm': errors.tolist(),
            'fitted_spans_cm': fitted.tolist(),
            'fitted_span_scales_cm': (z[:3]*uK).tolist(),
            'K_cm': float(K), 'K_reading_scale_cm': float(uK),
            'normalized_residuals': residuals.tolist(),
            'residual_plot_error_bars': [1., 1., 1.],
            'weighted_chi_squared_diagnostic': Q,
            'degrees_of_freedom': 2,
            'reduced_weighted_diagnostic': Q/2,
            'wavelength_assumed_m': wavelength,
            'wire_screen_separation_m': L,
            'thin_diameter_um': float(w*1e6),
            'thin_diameter_reading_scale_um': float(uw*1e6),
            'thin_equivalent_slit_central_width_cm': float(K),
            'thin_adjacent_one_side_minima_cm': float(K/2),
            'thick': {
                'interpretation': '4-4 denotes opposite fourth bright maxima',
                'recorded_span_cm': thick_span, 'reading_scale_cm': thick_error,
                'K_cm': float(thick_K), 'K_reading_scale_cm': float(thick_uK),
                'diameter_um': float(thick_w*1e6),
                'diameter_reading_scale_um': float(thick_uw*1e6),
                'adjacent_one_side_minima_cm': float(thick_K/2),
            },
        },
        'double_slit': {
            'labels_confirmed_by_user': ['222', '224'],
            'first_input_block_interpreted_as': '224',
            'center_separation_to_width_ratio': {'222': 2, '224': 3},
            'first_missing_bright_order': {'222': 2, '224': 3},
            '224_fine_first_two_K_cm_per_order': float(fine_K),
            '224_fine_first_two_uK_cm_per_order': float(fine_uK),
            '224_fine_first_two_weighted_diagnostic': float(np.sum(fine_residuals**2)),
            '224_envelope_first_two_K_cm': float(envelope_K),
            '224_envelope_first_two_uK_cm': float(envelope_uK),
            '224_predicted_third_envelope_maximum_cm': float(third_prediction),
            '224_predicted_third_envelope_maximum_scale_cm': float(third_u),
            '224_third_envelope_recorded_cm': 3.12,
            '224_third_feature_discrepancy_in_combined_reading_scales': float(discrepancy),
            'common_geometry_expected_fine_spacing_ratio_224_to_222': 2/3,
            'linear_fits': {
                'fine_224': fit_summary([1., 2.], [.25, .46], [.05, .05]),
                'envelope_224': fit_summary(z[:2], [.8, 1.35], [.1, .05]),
            },
        },
        'assumptions': [
            'The user confirmed maxima, superseding minima in input.tex.',
            'Opposite-side spans follow the repeated earlier procedure.',
            'The first input block is treated as 224 after the plate-label correction.',
            'The thick 4-4 entry is interpreted as opposite fourth maxima.',
            'Red-laser wavelength comes from the Lab 2 equipment specification.',
            'Bench position and wavelength uncertainties were not supplied and are held fixed.',
            'The previous lens location is upstream of the wire if retained.',
            'Missing or ambiguous values are not imputed.',
            'Chi squared is reported as a diagnostic because reading scales are estimates.',
            'Experiment 5 plate position is unrecorded, so absolute slit dimensions are not inferred.',
        ],
    }
    wire_rows = []
    for order, value, error in zip([1, 2, 3], distances, errors):
        wire_rows.append(dict(wire='thin', original_label=str(order), side_maximum_order=order,
                              span_cm=value, reading_scale_cm=error, used_for_calculation='yes', note='opposite-side interpretation'))
    wire_rows += [
        dict(wire='thick', original_label='3-7 Maximum', side_maximum_order='', span_cm=.048,
             reading_scale_cm=.05, used_for_calculation='no', note='ambiguous interval'),
        dict(wire='thick', original_label='4-4', side_maximum_order=4, span_cm=1.15,
             reading_scale_cm=.4, used_for_calculation='conditional', note='interpreted as opposite fourth maxima'),
        dict(wire='thick', original_label='1-5', side_maximum_order='', span_cm='',
             reading_scale_cm=.048, used_for_calculation='no', note='central value missing'),
    ]
    write_csv(data/'wire_measurements.csv', list(wire_rows[0]), wire_rows)
    double_rows = []
    groups = [
        ('224', '226', 'fine', [.25, .46, .65], [.05, .05, .2]),
        ('224', '226', 'envelope', [.8, 1.35, 3.12], [.1, .05, .2]),
        ('222', '222', 'fine', [.11, None, .65], [.05, .05, .2]),
        ('222', '222', 'envelope', [.25, .46, .65], [.05, .05, .2]),
    ]
    for pattern, raw_pattern, kind, values, scales in groups:
        for order, value, error in zip([1, 2, 3], values, scales):
            note = 'complete reading'
            use = 'yes' if pattern == '224' and order < 3 else 'no'
            if value is None:
                note = 'incomplete 0. entry, not interpreted as zero'
            elif pattern == '222' and kind == 'envelope':
                note = 'duplicates first pattern fine-fringe block'
            elif order == 3:
                note = 'outer feature/order assignment uncertain'
            double_rows.append(dict(pattern=pattern, original_pattern_label=raw_pattern, feature=kind,
                                    recorded_order=order, span_cm='' if value is None else value,
                                    reading_scale_cm=error, used_for_scale_fit=use, note=note))
    write_csv(data/'double_slit_measurements.csv', list(double_rows[0]), double_rows)
    (root/'analysis_results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    return results


if __name__ == '__main__':
    result = run_analysis()
    print('Thin diameter: %.12g micrometers' % result['wire']['thin_diameter_um'])
    print('Thin slit central width: %.12g cm' % result['wire']['K_cm'])
    print('Reduced weighted mismatch: %.12g' % result['wire']['reduced_weighted_diagnostic'])
    print('Third envelope discrepancy: %.12g quoted error scales' % result['double_slit']['224_third_feature_discrepancy_in_combined_reading_scales'])
