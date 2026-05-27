from rest_framework.renderers import JSONRenderer

class EnvelopeJSONRenderer(JSONRenderer):
    """
    Renders DRF responses in a consistent JSON envelope:
    {
      "data": {...} or [...],
      "meta": {"count": N, "next": "...", "previous": "..."},
      "errors": []
    }
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response') if renderer_context else None
        
        # If response was an exception or error, it was already formatted as
        # {"errors": [...], "data": None} by custom_exception_handler.
        if isinstance(data, dict) and 'errors' in data and 'data' in data:
            return super().render(data, accepted_media_type, renderer_context)

        envelope = {
            "errors": [],
            "data": data,
            "meta": {}
        }

        # Handle Paginated Responses
        if isinstance(data, dict) and 'results' in data:
            envelope["data"] = data["results"]
            envelope["meta"] = {
                "count": data.get("count", 0),
                "next": data.get("next"),
                "previous": data.get("previous")
            }
        elif isinstance(data, list):
            envelope["meta"] = {
                "count": len(data)
            }

        return super().render(envelope, accepted_media_type, renderer_context)
