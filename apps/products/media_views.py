import os
import mimetypes
from django.http import HttpResponse, Http404, StreamingHttpResponse
from django.conf import settings

def stream_media_view(request, path):
    """
    High-performance media streaming view that supports:
    1. HTTP 206 Partial Content (Byte-Range requests) for videos (.mp4, .webm, .mov).
       Enables browsers to start instant playback without downloading the full video file.
    2. Long-term Cache-Control headers for images and videos.
    3. Accept-Ranges: bytes header for video scrubbing.
    """
    media_root = os.path.abspath(str(settings.MEDIA_ROOT))
    full_path = os.path.abspath(os.path.join(media_root, path))

    # Security check: prevent directory traversal attacks using canonical common path
    try:
        if os.path.commonpath([media_root, full_path]) != media_root:
            raise Http404("Media file not found")
    except ValueError:
        raise Http404("Media file not found")

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise Http404("Media file not found")

    file_size = os.path.getsize(full_path)
    content_type, _ = mimetypes.guess_type(full_path)
    content_type = content_type or "application/octet-stream"

    # Block execution of active content (HTML, SVG scripts, etc.) if requested via media stream
    disallow_inline_types = ["text/html", "text/javascript", "application/javascript", "image/svg+xml"]
    is_active_content = any(content_type.lower().startswith(t) for t in disallow_inline_types)

    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = None
    if range_header.startswith("bytes="):
        range_match = range_header[6:].split('-')

    if range_match:
        try:
            start_str = range_match[0].strip()
            end_str = range_match[1].strip() if len(range_match) > 1 else ""

            if start_str and not end_str:
                start = int(start_str)
                end = file_size - 1
            elif not start_str and end_str:
                start = max(0, file_size - int(end_str))
                end = file_size - 1
            elif start_str and end_str:
                start = int(start_str)
                end = int(end_str)
            else:
                start = 0
                end = file_size - 1

            if start >= file_size or end >= file_size or start > end:
                resp = HttpResponse(status=416)
                resp['Content-Range'] = f'bytes */{file_size}'
                return resp

            chunk_size = 1024 * 512  # 512KB chunks
            content_length = (end - start) + 1

            def file_iterator(file_name, offset, length, chunk_sz=chunk_size):
                with open(file_name, 'rb') as f:
                    f.seek(offset)
                    remaining = length
                    while remaining > 0:
                        read_bytes = min(remaining, chunk_sz)
                        data = f.read(read_bytes)
                        if not data:
                            break
                        remaining -= len(data)
                        yield data

            response = StreamingHttpResponse(
                file_iterator(full_path, start, content_length),
                status=206,
                content_type=content_type,
            )
            response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response['Content-Length'] = str(content_length)
            response['Accept-Ranges'] = 'bytes'
            response['Cache-Control'] = 'public, max-age=31536000, immutable'
            response['X-Content-Type-Options'] = 'nosniff'
            if is_active_content:
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(full_path)}"'
            return response
        except ValueError:
            pass

    # Non-range request (images or full video downloads)
    def full_iterator(file_name, chunk_sz=1024 * 512):
        with open(file_name, 'rb') as f:
            while True:
                data = f.read(chunk_sz)
                if not data:
                    break
                yield data

    response = StreamingHttpResponse(full_iterator(full_path), content_type=content_type)
    response['Content-Length'] = str(file_size)
    response['Accept-Ranges'] = 'bytes'
    response['Cache-Control'] = 'public, max-age=31536000, immutable'
    response['X-Content-Type-Options'] = 'nosniff'
    if is_active_content:
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(full_path)}"'
    return response

