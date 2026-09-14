from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from monitoring.views import IngestView
from common.reads import RecentRecordsMixin
from monitoring.models import Mode
from .models import ModelVersion
from .serializers import ModelVersionSerializer, AnomalyResultSerializer


class ModelQuery(serializers.Serializer):
    id = serializers.UUIDField()
    source_id = serializers.UUIDField()
    mode = serializers.ChoiceField(choices=Mode.choices)


class ModelVersionView(IngestView):
    serializer_class = ModelVersionSerializer

    def get(self, request):
        query = ModelQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        p = query.validated_data
        obj = ModelVersion.objects.filter(id=p["id"], manifest__profile__source_id=str(p["source_id"]), manifest__profile__mode=p["mode"]).first()
        if obj is None:
            raise NotFound("Model not found for requested source/mode")
        return Response(self.serializer_class(obj).data)


class AnomalyResultView(RecentRecordsMixin, IngestView):
    serializer_class = AnomalyResultSerializer
    time_field = "observed_at"
