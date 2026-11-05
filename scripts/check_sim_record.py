"""Check configurable native state arrays; no mechanical acceptance inference."""
import argparse
import math
from pathlib import Path
import json

from _evidence import check_new_report, emit, sha256


def inspect_record(path, time_key, pose_key, deform_keys=(), time_column=None,
                   quaternion_order='xyzw', quaternion_tolerance=0.01, frame_map=None):
    import numpy as np

    path = Path(path)
    errors = []
    report = {'source_sha256': sha256(path), 'validation_scope': 'Record structure only; not physical acceptance',
              'quaternion_order': quaternion_order, 'quaternion_norm_tolerance': quaternion_tolerance,
              'arrays': {}, 'errors': errors}
    if not math.isfinite(quaternion_tolerance) or quaternion_tolerance < 0:
        raise ValueError('Quaternion tolerance must be finite and nonnegative')
    with np.load(path, allow_pickle=False) as data:
        # Object/pickle arrays are never loaded. Additional keys are untouched.
        for key in [time_key, pose_key, *deform_keys]:
            if key not in data:
                raise ValueError('Missing array: ' + key)
        raw_time = data[time_key]
        if time_column is not None:
            if raw_time.ndim != 2 or not 0 <= time_column < raw_time.shape[1]:
                raise ValueError('Time column requires an existing column in a 2-D array')
            times = raw_time[:, time_column]
        else:
            times = raw_time
        if times.ndim != 1 or len(times) < 2:
            raise ValueError('Time must contain at least two samples in a 1-D array')
        if times.dtype.kind not in 'fiu':
            raise ValueError('Time samples must be real numeric values')
        times = times.astype(np.float64)
        if not np.isfinite(times).all() or not np.all(np.diff(times) > 0):
            raise ValueError('Time samples must be finite and strictly increasing')
        report.update(samples=len(times), start_s=float(times[0]), end_s=float(times[-1]),
                      duration_s=float(times[-1] - times[0]),
                      sample_interval_s={'min': float(np.diff(times).min()), 'max': float(np.diff(times).max())})
        for key, width in [(pose_key, 7), *[(key, 3) for key in deform_keys]]:
            a = data[key]
            report['arrays'][key] = {'shape': list(a.shape), 'dtype': str(a.dtype)}
            if a.dtype.kind not in 'fiu' or a.ndim < 2 or a.shape[0] != len(times) or a.shape[-1] != width or a.size == 0:
                errors.append(key + ': expected nonempty real array (samples, ..., %d)' % width)
                continue
            if not np.isfinite(a).all():
                errors.append(key + ': contains non-finite states')
                continue
            if key == pose_key:
                norms = np.linalg.norm(a[..., 3:7].astype(np.float64), axis=-1)
                deviation = float(np.max(np.abs(norms - 1.)))
                report['max_quaternion_norm_error'] = deviation
                if deviation > quaternion_tolerance:
                    errors.append(key + ': quaternion norms exceed tolerance')
        if frame_map is not None:
            indices = json.loads(Path(frame_map).read_text(encoding='utf-8'))
            if not isinstance(indices, list) or not indices or any(
                    type(i) is not int or not 0 <= i < len(times) for i in indices):
                errors.append('Frame map must be a nonempty list of integer sample indices in range')
            else:
                report['frame_map'] = {'sha256': sha256(frame_map), 'frames': len(indices),
                                       'first_index': indices[0], 'last_index': indices[-1]}
    report['status'] = 'FAIL' if errors else 'PASS'
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    parser.add_argument('--time-key', required=True)
    parser.add_argument('--time-column', type=int)
    parser.add_argument('--pose-key', required=True)
    parser.add_argument('--deform-key', action='append', default=[])
    parser.add_argument('--quaternion-order', choices=['xyzw', 'wxyz'], default='xyzw')
    parser.add_argument('--quaternion-tolerance', type=float, default=.01)
    parser.add_argument('--frame-map', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        check_new_report(args.report)
        report = inspect_record(args.record, args.time_key, args.pose_key, args.deform_key,
                                args.time_column, args.quaternion_order, args.quaternion_tolerance, args.frame_map)
        emit(report, args.report)
        return int(report['status'] != 'PASS')
    except (ValueError, OSError, ImportError) as exc:
        parser.exit(2, 'Record check failed: %s\n' % exc)


if __name__ == '__main__':
    raise SystemExit(main())
