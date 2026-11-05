"""Make a decoded, looping preview from real video frames with FFmpeg."""
import argparse
import json
import math
from pathlib import Path
import subprocess
import tempfile

from _evidence import check_new_report, emit, sha256


def run(command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def probe(path, ffprobe):
    return json.loads(run([str(ffprobe), '-v', 'error', '-select_streams', 'v:0', '-count_frames',
                           '-show_entries', 'stream=width,height,nb_read_frames,duration:format=duration',
                           '-of', 'json', str(path)]).stdout)


def make_gif(source, output, ffmpeg, ffprobe, width=960, fps=8., colors=128, crop=None):
    source = Path(source).resolve()
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Output already exists: ' + str(output))
    if not source.is_file():
        raise ValueError('Input video does not exist')
    if source.suffix.lower() not in ['.mp4', '.mov', '.mkv', '.webm', '.avi', '.m4v']:
        raise ValueError('Input must be a local video file')
    if output.suffix.lower() != '.gif':
        raise ValueError('Output must end in .gif')
    if width < 16 or not math.isfinite(fps) or not 0 < fps <= 50 or not 4 <= colors <= 256:
        raise ValueError('Require width >=16, 0 < fps <=50 and 4 <= colors <=256')
    source_info = probe(source, ffprobe)
    streams = source_info.get('streams', [])
    if len(streams) != 1:
        raise ValueError('Input has no first video stream')
    filters = []
    if crop is not None:
        if len(crop) != 4 or any(type(x) is not int for x in crop):
            raise ValueError('Crop must be four integer values: x y width height')
        x, y, w, h = crop
        if min(x, y) < 0 or min(w, h) <= 0 or x + w > streams[0]['width'] or y + h > streams[0]['height']:
            raise ValueError('Crop falls outside the video')
        filters.append('crop=%d:%d:%d:%d' % (w, h, x, y))
    filters += ['fps=%.8g' % fps, 'scale=%d:-1:flags=lanczos' % width]
    base = ','.join(filters)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Reserve only this run's output. FFmpeg writes a temporary; final output is
    # published only after all frames decode. Existing user data is never removed.
    with output.open('xb'):
        pass
    try:
        with tempfile.TemporaryDirectory(prefix='video-preview-') as temporary:
            palette = Path(temporary) / 'palette.png'
            staged = Path(temporary) / 'preview.gif'
            run([str(ffmpeg), '-y', '-v', 'error', '-xerror', '-i', str(source), '-map', '0:v:0',
                 '-vf', base + ',palettegen=max_colors=%d:stats_mode=diff' % colors,
                 '-frames:v', '1', '-threads', '1', str(palette)])
            run([str(ffmpeg), '-y', '-v', 'error', '-xerror', '-i', str(source), '-i', str(palette),
                 '-filter_complex', '[0:v:0]' + base + '[v];[v][1:v]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle',
                 '-an', '-loop', '0', str(staged)])
            run([str(ffmpeg), '-v', 'error', '-xerror', '-i', str(staged), '-f', 'null', '-'])
            info = probe(staged, ffprobe)
            stream = info['streams'][0]
            frames = int(stream['nb_read_frames'])
            duration = float(info.get('format', {}).get('duration', stream.get('duration', 0)))
            if frames < 2 or not math.isfinite(duration) or duration <= 0:
                raise ValueError('Preview must contain at least two decoded frames and positive duration')
            # Copy across filesystems into the reserved output, after validation.
            with staged.open('rb') as src, output.open('wb') as dst:
                import shutil
                shutil.copyfileobj(src, dst)
        return {'source_sha256': sha256(source), 'source_video': source.name,
                'source_probe': source_info, 'output_sha256': sha256(output), 'bytes': output.stat().st_size,
                'resolution': [stream['width'], stream['height']], 'frames': frames, 'duration_s': duration,
                'requested_fps': fps, 'palette_colors': colors, 'crop_xywh': crop,
                'loop': 0, 'all_frames_decoded': True, 'motion_interpolation': False,
                'validation_scope': 'Media conversion only; source physics provenance must be supplied separately'}
    except BaseException:
        output.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--ffprobe', default='ffprobe')
    parser.add_argument('--width', type=int, default=960)
    parser.add_argument('--fps', type=float, default=8.)
    parser.add_argument('--colors', type=int, default=128)
    parser.add_argument('--crop', nargs=4, type=int, metavar=('X', 'Y', 'WIDTH', 'HEIGHT'))
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        if args.report is not None and args.report.resolve() == args.output.resolve():
            raise ValueError('Report and GIF must have different paths')
        check_new_report(args.report)
        report = make_gif(args.source, args.output, args.ffmpeg, args.ffprobe,
                          args.width, args.fps, args.colors, args.crop)
        emit(report, args.report)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr[-1500:] if isinstance(exc, subprocess.CalledProcessError) and exc.stderr else str(exc)
        parser.exit(2, 'Preview generation failed: %s\n' % detail)


if __name__ == '__main__':
    main()
