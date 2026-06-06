from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from audits.executive_dashboard import get_executive_dashboard


@login_required
def demo_dashboard(request):
    """
    Vista principal de demostración — F6-01
    Muestra el dashboard ejecutivo completo como punto de entrada
    del recorrido de defensa del TFG.
    """
    standard_id = request.GET.get('standard_id')
    if standard_id:
        standard_id = int(standard_id)

    dashboard_data = get_executive_dashboard(standard_id=standard_id)

    from standards.models import Standard
    standards = Standard.objects.filter(is_active=True)

    return render(request, 'mistemplates/demo/f6_01_dashboard.html', {
        'dashboard_data': dashboard_data,
        'standards': standards,
        'selected_standard_id': standard_id,
    })

@login_required
def demo_normative_catalog(request):
    """
    Vista del catálogo normativo — F6-02
    Muestra normas, cláusulas, requisitos y trazabilidad ISO 9001 ↔ AS9100.
    """
    from standards.models import Standard, Clause, StandardRequirement, StandardMapping

    standards = Standard.objects.filter(is_active=True).order_by('id')

    selected_standard_id = request.GET.get('standard_id')
    selected_clause_id = request.GET.get('clause_id')

    if selected_standard_id:
        selected_standard_id = int(selected_standard_id)
        selected_standard = Standard.objects.filter(
            id=selected_standard_id
        ).first()
    else:
        selected_standard = standards.first()
        if selected_standard:
            selected_standard_id = selected_standard.id

    # Cláusulas raíz de la norma seleccionada
    root_clauses = []
    if selected_standard:
        root_clauses = list(
            Clause.objects.filter(
                standard=selected_standard,
                parent__isnull=True
            ).order_by('ordering')
        )

    # Cláusula seleccionada y sus requisitos
    selected_clause = None
    clause_requirements = []
    child_clauses = []
    mappings = []

    if selected_clause_id:
        selected_clause = Clause.objects.filter(
            id=selected_clause_id
        ).select_related('standard', 'parent').first()

        if selected_clause:
            clause_requirements = list(
                StandardRequirement.objects.filter(
                    clause=selected_clause
                ).order_by('ordering')
            )
            child_clauses = list(
                Clause.objects.filter(
                    parent=selected_clause
                ).order_by('ordering')
            )

            # Mapeos para los requisitos de esta cláusula
            req_ids = [r.id for r in clause_requirements]
            mappings = list(
                StandardMapping.objects.filter(
                    source_requirement_id__in=req_ids
                ).select_related(
                    'source_requirement__clause__standard',
                    'target_requirement__clause__standard',
                ) | StandardMapping.objects.filter(
                    target_requirement_id__in=req_ids
                ).select_related(
                    'source_requirement__clause__standard',
                    'target_requirement__clause__standard',
                )
            )

    # Resumen de mapeos entre normas
    mapping_summary = {
        'total': StandardMapping.objects.count(),
        'equivalent': StandardMapping.objects.filter(
            mapping_type='EQUIVALENT'
        ).count(),
        'superset': StandardMapping.objects.filter(
            mapping_type='SUPERSET'
        ).count(),
        'no_equivalent': StandardMapping.objects.filter(
            mapping_type='NO_EQUIVALENT'
        ).count(),
    }

    # Estadísticas de la norma seleccionada
    standard_stats = {}
    if selected_standard:
        total_reqs = StandardRequirement.objects.filter(
            clause__standard=selected_standard
        ).count()
        mandatory_reqs = StandardRequirement.objects.filter(
            clause__standard=selected_standard,
            mandatory=True
        ).count()
        high_criticality = StandardRequirement.objects.filter(
            clause__standard=selected_standard,
            criticality_level='high'
        ).count()
        extensions = StandardRequirement.objects.filter(
            clause__standard=selected_standard,
            is_extension=True
        ).count()

        standard_stats = {
            'total_clauses': Clause.objects.filter(
                standard=selected_standard
            ).count(),
            'total_requirements': total_reqs,
            'mandatory_requirements': mandatory_reqs,
            'high_criticality': high_criticality,
            'extensions': extensions,
        }

    return render(request, 'mistemplates/demo/f6_02_normativo.html', {
        'standards': standards,
        'selected_standard': selected_standard,
        'selected_standard_id': selected_standard_id,
        'root_clauses': root_clauses,
        'selected_clause': selected_clause,
        'selected_clause_id': selected_clause_id,
        'clause_requirements': clause_requirements,
        'child_clauses': child_clauses,
        'mappings': mappings,
        'mapping_summary': mapping_summary,
        'standard_stats': standard_stats,
    })

def _get_gap_analysis_data(annual_plan):
    """
    Calcula el análisis de brechas para un plan de auditoría.
    Replica la lógica de audits/views.py::get_gap_analysis
    pero devuelve un dict en lugar de JsonResponse.
    """
    from audits.models import ProcessRequirement, Checklist

    process = annual_plan.annual_program.process
    standard = annual_plan.annual_program.standard

    if not standard:
        return None

    process_requirements = ProcessRequirement.objects.filter(
        process=process,
        requirement__clause__standard=standard
    ).select_related('requirement__clause__standard')

    if not process_requirements.exists():
        return None

    checklist_items = Checklist.objects.filter(
        audit_plan=annual_plan
    ).select_related('question__requirement__requirement__clause')

    checklist_index = {}
    for item in checklist_items:
        if item.question and item.question.requirement:
            pr_id = item.question.requirement.id
            checklist_index[pr_id] = item

    gaps = []
    summary = {
        'compliant_count': 0,
        'non_compliant_count': 0,
        'insufficient_count': 0,
        'not_evaluated_count': 0,
    }

    for pr in process_requirements.order_by(
        'requirement__clause__ordering',
        'requirement__ordering'
    ):
        req = pr.requirement
        clause = req.clause
        checklist_item = checklist_index.get(pr.id)

        if checklist_item is None:
            status = 'NOT_EVALUATED'
            summary['not_evaluated_count'] += 1
        elif checklist_item.compliance:
            status = 'COMPLIANT'
            summary['compliant_count'] += 1
        elif checklist_item.evidence and checklist_item.evidence.strip():
            status = 'NON_COMPLIANT'
            summary['non_compliant_count'] += 1
        else:
            status = 'INSUFFICIENT_EVIDENCE'
            summary['insufficient_count'] += 1

        gaps.append({
            'status': status,
            'requirement_text': req.text,
            'criticality_level': req.criticality_level,
            'mandatory': req.mandatory,
            'clause_code': clause.code,
            'clause_title': clause.title,
        })

    return {
        'summary': summary,
        'gaps': gaps,
    }

@login_required
def demo_audit_checklists(request):
    """
    Vista de auditorías y checklists dinámicos — F6-03
    Muestra el flujo de auditoría con trazabilidad normativa y análisis de brechas.
    """
    from audits.models import (
        AnnualPlan, Checklist, Findings, AnnualProgram
    )
    

    # Selector de plan
    selected_plan_id = request.GET.get('plan_id')
    if selected_plan_id:
        selected_plan_id = int(selected_plan_id)

    # Todos los planes con checklist disponible
    plans_with_data = []
    for plan in AnnualPlan.objects.select_related(
        'annual_program__process',
        'annual_program__standard'
    ).order_by('id'):
        checklist_count = Checklist.objects.filter(
            audit_plan=plan
        ).count()
        if checklist_count > 0:
            plans_with_data.append({
                'id': plan.id,
                'process_name': plan.annual_program.process.name,
                'standard_name': plan.annual_program.standard.name
                    if plan.annual_program.standard else '—',
                'opening_date': plan.audit_opening_date,
                'checklist_count': checklist_count,
            })

    selected_plan = None
    checklist_items = []
    gap_analysis = None
    findings = []
    stats = {}

    if selected_plan_id:
        try:
            selected_plan = AnnualPlan.objects.select_related(
                'annual_program__process',
                'annual_program__standard'
            ).get(id=selected_plan_id)

            # Checklist con trazabilidad normativa
            raw_checklist = Checklist.objects.filter(
                audit_plan=selected_plan
            ).select_related(
                'question__requirement__requirement__clause__standard'
            ).order_by('orden')

            for item in raw_checklist:
                req = None
                clause_code = '—'
                clause_title = '—'
                req_text = '—'
                criticality = 'low'
                mandatory = False

                try:
                    pr = item.question.requirement
                    req = pr.requirement
                    clause_code = req.clause.code
                    clause_title = req.clause.title
                    req_text = req.text
                    criticality = req.criticality_level
                    mandatory = req.mandatory
                except Exception:
                    pass

                checklist_items.append({
                    'id': item.id,
                    'orden': item.orden,
                    'question_text': item.question.question_text,
                    'compliance': item.compliance,
                    'evidence': item.evidence or '',
                    'clause_code': clause_code,
                    'clause_title': clause_title,
                    'req_text': req_text,
                    'criticality': criticality,
                    'mandatory': mandatory,
                })

            # Análisis de brechas
            gap_analysis = _get_gap_analysis_data(selected_plan)

            # Hallazgos
            findings = list(Findings.objects.filter(
                audit_plan=selected_plan
            ).select_related('requirement__requirement__clause'))

            # Estadísticas del checklist
            total = len(checklist_items)
            compliant = sum(1 for i in checklist_items if i['compliance'])
            non_compliant = sum(
                1 for i in checklist_items
                if not i['compliance'] and i['evidence']
            )
            insufficient = sum(
                1 for i in checklist_items
                if not i['compliance'] and not i['evidence']
            )
            stats = {
                'total': total,
                'compliant': compliant,
                'non_compliant': non_compliant,
                'insufficient': insufficient,
                'compliance_rate': round(
                    compliant / total * 100, 1
                ) if total > 0 else 0,
            }

        except AnnualPlan.DoesNotExist:
            selected_plan = None

    return render(request, 'mistemplates/demo/f6_03_auditorias.html', {
        'plans_with_data': plans_with_data,
        'selected_plan_id': selected_plan_id,
        'selected_plan': selected_plan,
        'checklist_items': checklist_items,
        'gap_analysis': gap_analysis,
        'findings': findings,
        'stats': stats,
    })

@login_required
def demo_compliance(request):
    return render(request, 'mistemplates/demo/f6_04_cumplimiento.html', {})

@login_required
def demo_analytics(request):
    return render(request, 'mistemplates/demo/f6_05_analitica.html', {})