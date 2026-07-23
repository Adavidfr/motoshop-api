# motoshop/migrations/0006_devolucion_idempotencia.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('motoshop', '0005_flujo_comercial_servicios'),
    ]

    operations = [
        migrations.AddField(
            model_name='devolucion',
            name='monto_reembolso_aplicado',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Monto reembolsado al aprobar (0 si no hubo pagos).',
                max_digits=12,
            ),
        ),
        migrations.AddField(
            model_name='devolucion',
            name='stock_reintegrado',
            field=models.BooleanField(default=False),
        ),
    ]
