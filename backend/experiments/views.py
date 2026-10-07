import json
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import ParseError
from . import services, validation as v


class StrictJSONParser(JSONParser):
    """Reject duplicate fields and non-finite constants rather than last-key wins."""
    def parse(self, stream, media_type=None, parser_context=None):
        def pairs(items):
            value = {}
            for key, child in items:
                if key in value:
                    raise ValueError("duplicate")
                value[key] = child
            return value
        try:
            return json.load(stream, object_pairs_hook=pairs,
                             parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
        except (ValueError, UnicodeError, RecursionError):
            raise ParseError("Expected bounded JSON with unique keys and finite values.") from None


class LabView(APIView):
    parser_classes = [StrictJSONParser]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.query_params:
            v.fail("Query parameters are not supported.")


class JobsView(LabView):
    def get(self, request):
        return Response({"jobs": services.listing()})

    def post(self, request):
        v.keys(request.data, ("config",))
        return Response(services.create(v.config(request.data["config"])), status=201)


class JobView(LabView):
    def get(self, request, job_id):
        return Response(services.detail(job_id))


class CancelView(LabView):
    def post(self, request, job_id):
        v.keys(request.data, ())
        return Response(services.cancel(job_id))


class ClaimView(LabView):
    def post(self, request):
        v.keys(request.data, ())
        return Response(services.claim())


class HeartbeatView(LabView):
    def post(self, request, job_id):
        data = request.data
        v.keys(data, ("lease_token", "stage"), ("completed", "total"))
        v.lease(data["lease_token"])
        if not isinstance(data["stage"], str) or not re.fullmatch(r"[a-z][a-z0-9_ -]{0,47}", data["stage"]):
            v.fail("Invalid progress stage.")
        completed, total = data.get("completed"), data.get("total")
        for value in (completed, total):
            v.number(value, 0, 2000000, nullable=True, integer=True)
        if completed is not None and (total is None or completed > total):
            v.fail("Progress must have a total and cannot exceed it.")
        return Response(services.heartbeat(job_id, data["lease_token"], data["stage"], completed, total))


class FinishView(LabView):
    def post(self, request, job_id):
        data = request.data
        v.keys(data, ("lease_token", "status"), ("result", "error"))
        v.lease(data["lease_token"])
        if data["status"] not in ("SUCCEEDED", "FAILED", "CANCELLED"):
            v.fail("Invalid terminal status.")
        result = data.get("result")
        if data["status"] == "SUCCEEDED":
            result = v.result(result)
            if data.get("error"):
                v.fail("Successful results cannot include an error.")
        elif result is not None:
            v.fail("Only successful jobs can include results.")
        v.text(data.get("error", ""), 200)
        # Never persist arbitrary child exceptions: paths, env tokens and other
        # sensitive details can be embedded in library messages.
        error = "Experiment failed in the local worker. Review local setup and start a new run." if data["status"] == "FAILED" else ""
        return Response(services.finish(job_id, data["lease_token"], data["status"], result, error))
