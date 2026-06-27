# Generated manually after merge conflict resolution
# Combines 0001_initial from both branches (HEAD + origin/david_tarea2)

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── Inventario (rama HEAD) ──────────────────────────────────────────
        migrations.CreateModel(
            name='CategoriaMoto',
            fields=[
                ('id_categoria', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Categoría de Moto',
                'verbose_name_plural': 'Categorías de Motos',
                'db_table': 'categorias_moto',
            },
        ),
        migrations.CreateModel(
            name='Marca',
            fields=[
                ('id_marca', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=150)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Marca',
                'verbose_name_plural': 'Marcas',
                'db_table': 'marcas',
            },
        ),
        migrations.CreateModel(
            name='Repuesto',
            fields=[
                ('id_repuesto', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=150)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('sku', models.CharField(max_length=50, unique=True)),
                ('costo', models.DecimalField(decimal_places=2, max_digits=12)),
                ('precio_venta', models.DecimalField(decimal_places=2, max_digits=12)),
                ('stock', models.IntegerField()),
                ('estado', models.CharField(max_length=50)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Repuesto',
                'verbose_name_plural': 'Repuestos',
                'db_table': 'repuestos',
            },
        ),
        migrations.CreateModel(
            name='Moto',
            fields=[
                ('id_moto', models.AutoField(primary_key=True, serialize=False)),
                ('modelo', models.CharField(max_length=150)),
                ('anio', models.IntegerField()),
                ('cilindraje', models.IntegerField()),
                ('color', models.CharField(max_length=50)),
                ('precio', models.DecimalField(decimal_places=2, max_digits=12)),
                ('stock', models.IntegerField()),
                ('estado', models.CharField(max_length=30)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('categoria', models.ForeignKey(db_column='id_categoria', on_delete=django.db.models.deletion.PROTECT, related_name='motos', to='motoshop.categoriamoto')),
                ('marca', models.ForeignKey(db_column='id_marca', on_delete=django.db.models.deletion.PROTECT, related_name='motos', to='motoshop.marca')),
            ],
            options={
                'verbose_name': 'Moto',
                'verbose_name_plural': 'Motos',
                'db_table': 'motos',
            },
        ),
        migrations.CreateModel(
            name='MovimientoInventario',
            fields=[
                ('id_movimiento', models.AutoField(primary_key=True, serialize=False)),
                ('cantidad', models.IntegerField()),
                ('tipo_movimiento', models.CharField(max_length=50)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('fecha_movimiento', models.DateTimeField(auto_now_add=True)),
                ('moto', models.ForeignKey(blank=True, db_column='id_moto', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimientos', to='motoshop.moto')),
                ('usuario', models.ForeignKey(db_column='id_usuario', on_delete=django.db.models.deletion.PROTECT, related_name='movimientos_inventario', to=settings.AUTH_USER_MODEL)),
                ('repuesto', models.ForeignKey(blank=True, db_column='id_repuesto', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimientos', to='motoshop.repuesto')),
            ],
            options={
                'verbose_name': 'Movimiento de Inventario',
                'verbose_name_plural': 'Movimientos de Inventario',
                'db_table': 'movimientos_inventario',
            },
        ),

        # ── Ventas / Carrito (rama david_tarea2) ───────────────────────────
        migrations.CreateModel(
            name='ClientePerfil',
            fields=[
                ('id_perfil', models.BigAutoField(primary_key=True, serialize=False)),
                ('cedula', models.CharField(blank=True, default='', max_length=20)),
                ('telefono', models.CharField(blank=True, default='', max_length=20)),
                ('direccion', models.TextField(blank=True, default='')),
                ('fecha_nacimiento', models.DateField(blank=True, null=True)),
                ('id_usuario', models.OneToOneField(db_column='id_usuario', on_delete=django.db.models.deletion.CASCADE, related_name='perfil_cliente', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'clientes_perfil',
            },
        ),
        migrations.CreateModel(
            name='CarritoCompras',
            fields=[
                ('id_carrito', models.BigAutoField(primary_key=True, serialize=False)),
                ('estado', models.CharField(choices=[('activo', 'Activo'), ('procesado', 'Procesado'), ('abandonado', 'Abandonado')], default='activo', max_length=30)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('id_usuario_cliente', models.ForeignKey(db_column='id_usuario_cliente', on_delete=django.db.models.deletion.CASCADE, related_name='carritos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'carrito_compras',
                'ordering': ['-fecha_creacion'],
            },
        ),
        migrations.CreateModel(
            name='ItemCarrito',
            fields=[
                ('id_item', models.BigAutoField(primary_key=True, serialize=False)),
                ('id_moto', models.IntegerField(blank=True, null=True)),
                ('id_repuesto', models.IntegerField(blank=True, null=True)),
                ('cantidad', models.PositiveIntegerField(default=1)),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=12)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('id_carrito', models.ForeignKey(db_column='id_carrito', on_delete=django.db.models.deletion.CASCADE, related_name='items', to='motoshop.carritocompras')),
            ],
            options={
                'db_table': 'items_carrito',
            },
        ),
        migrations.CreateModel(
            name='Pedido',
            fields=[
                ('id_pedido', models.BigAutoField(primary_key=True, serialize=False)),
                ('estado', models.CharField(choices=[('pending', 'Pendiente'), ('confirmed', 'Confirmado'), ('shipped', 'Enviado'), ('delivered', 'Entregado'), ('cancelled', 'Cancelado')], default='pending', max_length=30)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('fecha_pedido', models.DateTimeField(auto_now_add=True)),
                ('id_carrito', models.ForeignKey(blank=True, db_column='id_carrito', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pedidos', to='motoshop.carritocompras')),
                ('id_usuario_cliente', models.ForeignKey(db_column='id_usuario_cliente', on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'pedidos',
                'ordering': ['-fecha_pedido'],
            },
        ),
        migrations.CreateModel(
            name='Venta',
            fields=[
                ('id_venta', models.BigAutoField(primary_key=True, serialize=False)),
                ('total_venta', models.DecimalField(decimal_places=2, max_digits=12)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('completada', 'Completada'), ('anulada', 'Anulada')], default='pendiente', max_length=30)),
                ('fecha_venta', models.DateTimeField(auto_now_add=True)),
                ('id_pedido', models.OneToOneField(db_column='id_pedido', on_delete=django.db.models.deletion.PROTECT, related_name='venta', to='motoshop.pedido')),
                ('id_usuario_cliente', models.ForeignKey(db_column='id_usuario_cliente', on_delete=django.db.models.deletion.PROTECT, related_name='ventas_como_cliente', to=settings.AUTH_USER_MODEL)),
                ('id_usuario_vendedor', models.ForeignKey(db_column='id_usuario_vendedor', on_delete=django.db.models.deletion.PROTECT, related_name='ventas_como_vendedor', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'ventas',
                'ordering': ['-fecha_venta'],
            },
        ),
        migrations.CreateModel(
            name='Financiamiento',
            fields=[
                ('id_financiamiento', models.BigAutoField(primary_key=True, serialize=False)),
                ('entidad_financiera', models.CharField(max_length=100)),
                ('monto_financiado', models.DecimalField(decimal_places=2, max_digits=12)),
                ('tasa_interes', models.DecimalField(decimal_places=2, max_digits=5)),
                ('plazo_meses', models.PositiveIntegerField()),
                ('cuota_mensual', models.DecimalField(decimal_places=2, max_digits=12)),
                ('estado', models.CharField(choices=[('activo', 'Activo'), ('pagado', 'Pagado'), ('vencido', 'Vencido'), ('cancelado', 'Cancelado')], default='activo', max_length=30)),
                ('id_venta', models.ForeignKey(db_column='id_venta', on_delete=django.db.models.deletion.PROTECT, related_name='financiamientos', to='motoshop.venta')),
            ],
            options={
                'db_table': 'financiamientos',
            },
        ),
    ]
