# motoshop/serializers/documento_venta.py
from rest_framework import serializers
from motoshop.models import DocumentoVenta


class DocumentoVentaSerializer(serializers.ModelSerializer):
    """Serializer de documentos de venta con nombres exactos del esquema SQL."""

    class Meta:
        model  = DocumentoVenta
        fields = [
            'id_documento', 'id_venta',
            'tipo_documento', 'archivo_url', 'fecha_subida',
        ]
        read_only_fields = ['id_documento', 'fecha_subida']


class DocumentoVentaCreateSerializer(serializers.ModelSerializer):
    """Serializer para subir un documento a una venta."""

    class Meta:
        model  = DocumentoVenta
        fields = ['id_venta', 'tipo_documento', 'archivo_url']
