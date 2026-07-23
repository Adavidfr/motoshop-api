# motoshop/serializers/documento_venta.py
from rest_framework import serializers
from motoshop.models import DocumentoVenta, Venta


class DocumentoVentaSerializer(serializers.ModelSerializer):
    """
    Serializer de documentos de venta.

    archivo_url_legacy: solo lectura; plan de retiro documentado en DocumentoVentaService.
    """
    archivo_url = serializers.SerializerMethodField()
    archivo_url_legacy = serializers.CharField(read_only=True)
    subido_por_info = serializers.SerializerMethodField()

    class Meta:
        model  = DocumentoVenta
        fields = [
            'id_documento', 'id_venta', 'tipo_documento',
            'archivo_url', 'archivo_url_legacy',
            'nombre_original', 'tamano_bytes', 'content_type',
            'subido_por', 'subido_por_info', 'fecha_subida',
        ]
        read_only_fields = fields

    def get_archivo_url(self, obj):
        return obj.archivo_url

    def get_subido_por_info(self, obj):
        if not obj.subido_por_id:
            return None
        return {'id': obj.subido_por_id, 'username': obj.subido_por.username}


class DocumentoVentaCreateSerializer(serializers.Serializer):
    """Subida multipart de documento. archivo es obligatorio para documentos nuevos."""
    id_venta = serializers.PrimaryKeyRelatedField(queryset=Venta.objects.all())
    tipo_documento = serializers.ChoiceField(choices=DocumentoVenta.TIPO_CHOICES)
    archivo = serializers.FileField()

    def validate(self, attrs):
        legacy_fields = ('archivo_url', 'archivo_url_legacy')
        for campo in legacy_fields:
            if campo in self.initial_data:
                raise serializers.ValidationError(
                    {campo: 'No se acepta URL manual. Use el campo "archivo" (multipart).'},
                )
        return attrs
