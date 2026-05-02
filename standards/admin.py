from django.contrib import admin
from .models import Standard, Clause, StandardRequirement, StandardMapping


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'sector', 'is_active', 'created_at')
    list_filter = ('is_active', 'sector')
    search_fields = ('name', 'version')
    ordering = ('name',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'version', 'sector')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Clause)
class ClauseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'standard', 'parent', 'ordering')
    list_filter = ('standard',)
    search_fields = ('code', 'title')
    ordering = ('standard', 'ordering', 'code')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('standard', 'code', 'title', 'description')
        }),
        ('Jerarquía', {
            'fields': ('parent', 'ordering')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('standard', 'parent')


@admin.register(StandardRequirement)
class StandardRequirementAdmin(admin.ModelAdmin):
    list_display = ('get_clause_code', 'text_preview', 'mandatory', 'criticality_level', 'is_extension')
    list_filter = ('mandatory', 'criticality_level', 'is_extension', 'clause__standard')
    search_fields = ('text', 'clause__code', 'clause__title')
    ordering = ('clause__standard', 'clause__ordering', 'ordering')
    
    fieldsets = (
        ('Ubicación', {
            'fields': ('clause',)
        }),
        ('Contenido', {
            'fields': ('text', 'ordering')
        }),
        ('Propiedades', {
            'fields': ('mandatory', 'criticality_level', 'is_extension')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('clause', 'clause__standard')
    
    def get_clause_code(self, obj):
        return f"{obj.clause.standard.name} § {obj.clause.code}"
    get_clause_code.short_description = 'Referencia'
    get_clause_code.admin_order_field = 'clause__code'
    
    def text_preview(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Texto del Requisito'


@admin.register(StandardMapping)
class StandardMappingAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'mapping_type', 'created_at')
    list_filter = (
        'mapping_type',
        'source_requirement__clause__standard',
        'target_requirement__clause__standard'
    )
    search_fields = (
        'source_requirement__text',
        'target_requirement__text',
        'notes'
    )
    ordering = ('mapping_type',)

    fieldsets = (
        ('Requisitos', {
            'fields': ('source_requirement', 'target_requirement')
        }),
        ('Relación', {
            'fields': ('mapping_type', 'notes')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'source_requirement__clause__standard',
            'target_requirement__clause__standard'
        )