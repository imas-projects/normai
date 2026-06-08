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
    try:
        standard_id = int(standard_id) if standard_id else None
    except (ValueError, TypeError):
        standard_id = None

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

    try:
        selected_standard_id = int(selected_standard_id) if selected_standard_id else None
    except (ValueError, TypeError):
        selected_standard_id = None
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
    try:
        selected_plan_id = int(selected_plan_id) if selected_plan_id else None
    except (ValueError, TypeError):
        selected_plan_id = None

    # Todos los planes con checklist disponible
    plans_with_data = []
    for plan in AnnualPlan.objects.select_related(
        'annual_program__process',
        'annual_program__standard'
    ).order_by('id'):
        checklist_count = Checklist.objects.filter(
            audit_plan=plan
        ).count()
        plans_with_data.append({
            'id': plan.id,
            'process_name': plan.annual_program.process.name,
            'standard_name': plan.annual_program.standard.name
                if plan.annual_program.standard else '—',
            'opening_date': plan.audit_opening_date,
            'checklist_count': checklist_count,
            'has_checklist': checklist_count > 0,
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
    """
    Vista del motor de cumplimiento — F6-04
    Muestra snapshots, histórico temporal y comparación entre periodos.
    """
    from audits.models import ComplianceSnapshot
    from audits.compliance_engine import (
        get_compliance_history, compare_compliance_periods
    )
    from standards.models import Standard

    standards = Standard.objects.filter(is_active=True)
    processes_with_snapshots = []

    # Obtener procesos únicos con snapshots
    process_ids = list(set(
        ComplianceSnapshot.objects.values_list('process_id', flat=True)
    ))
    from processes.models import Process
    for pid in sorted(process_ids):
        try:
            p = Process.objects.get(id=pid)
            snap_count = ComplianceSnapshot.objects.filter(
                process_id=pid
            ).count()
            latest = ComplianceSnapshot.objects.filter(
                process_id=pid
            ).order_by('-calculated_at').first()
            processes_with_snapshots.append({
                'id': p.id,
                'name': p.name,
                'snap_count': snap_count,
                'latest_score': round(latest.score * 100, 1) if latest else 0,
                'latest_category': latest.category if latest else '—',
            })
        except Process.DoesNotExist:
            pass

    # Parámetros de selección
    selected_process_id = request.GET.get('process_id')
    selected_standard_id = request.GET.get('standard_id')
    selected_snapshot_a = request.GET.get('snap_a')
    selected_snapshot_b = request.GET.get('snap_b')
    active_tab = request.GET.get('tab', 'history')

    try:
        selected_process_id = int(selected_process_id) if selected_process_id else None
    except (ValueError, TypeError):
        selected_process_id = None
    if not selected_process_id and processes_with_snapshots:
        selected_process_id = processes_with_snapshots[0]['id']

    try:
        selected_standard_id = int(selected_standard_id) if selected_standard_id else None
    except (ValueError, TypeError):
        selected_standard_id = None
    if not selected_standard_id:
        # Buscar norma robustamente desde snapshots disponibles
        from audits.models import ComplianceSnapshot
        first_snap = ComplianceSnapshot.objects.select_related(
            'standard'
        ).order_by('id').first()
        if first_snap:
            selected_standard_id = first_snap.standard_id

    # Histórico del proceso seleccionado
    history_data = None
    chart_data = []
    snapshots_for_process = []

    if selected_process_id and selected_standard_id:
        history_result = get_compliance_history(
            selected_process_id, selected_standard_id
        )
        if history_result.get('success'):
            history_data = history_result
            for snap in history_result.get('history', []):
                chart_data.append({
                    'x': snap['calculated_at'][:10],
                    'y': snap['score'],
                    'category': snap['category'],
                    'snapshot_id': snap['id'],
                })

        # Snapshots disponibles para comparación
        snapshots_for_process = list(
            ComplianceSnapshot.objects.filter(
                process_id=selected_process_id,
                standard_id=selected_standard_id,
            ).order_by('-calculated_at').values(
                'id', 'score', 'category', 'calculated_at',
                'annual_plan_id', 'total_requirements',
                'compliant_count', 'non_compliant_count'
            )
        )
        for s in snapshots_for_process:
            s['score'] = round(s['score'] * 100, 1)

    # Comparación entre snapshots
    comparison_data = None
    if selected_snapshot_a and selected_snapshot_b:
        try:
            comparison_result = compare_compliance_periods(
                int(selected_snapshot_a),
                int(selected_snapshot_b)
            )
        except (ValueError, TypeError):
            comparison_result = {'error': 'IDs de snapshot no válidos.'}
        if comparison_result.get('success'):
            comparison_data = comparison_result

    # Detalle del snapshot seleccionado
    snapshot_detail = None
    selected_snapshot_id = request.GET.get('snapshot_id')
    if selected_snapshot_id:
        try:
            snap = ComplianceSnapshot.objects.select_related(
                'process', 'standard'
            ).get(id=int(selected_snapshot_id) if str(selected_snapshot_id).isdigit() else 0)
            snapshot_detail = {
                'id': snap.id,
                'process_name': snap.process.name,
                'standard_name': snap.standard.name,
                'score': round(snap.score * 100, 1),
                'category': snap.category,
                'calculated_at': snap.calculated_at,
                'total_requirements': snap.total_requirements,
                'compliant_count': snap.compliant_count,
                'non_compliant_count': snap.non_compliant_count,
                'insufficient_count': snap.insufficient_count,
                'not_evaluated_count': snap.not_evaluated_count,
                'detail': snap.detail,
            }
        except ComplianceSnapshot.DoesNotExist:
            pass

    latest_score = None
    latest_category = None
    if history_data and history_data.get('history'):
        last_snap = history_data['history'][-1]
        latest_score = last_snap.get('score')
        latest_category = last_snap.get('category')

    import json
    return render(request, 'mistemplates/demo/f6_04_cumplimiento.html', {
        'standards': standards,
        'processes_with_snapshots': processes_with_snapshots,
        'selected_process_id': selected_process_id,
        'selected_standard_id': selected_standard_id,
        'history_data': history_data,
        'chart_data_json': json.dumps(chart_data),
        'snapshots_for_process': snapshots_for_process,
        'selected_snapshot_a': selected_snapshot_a,
        'selected_snapshot_b': selected_snapshot_b,
        'comparison_data': comparison_data,
        'snapshot_detail': snapshot_detail,
        'selected_snapshot_id': selected_snapshot_id,
        'active_tab': active_tab,
        'latest_score': latest_score,
        'latest_category': latest_category,
    })

@login_required
def demo_analytics(request):
    """
    Vista de analítica predictiva — F6-05
    Muestra predicciones de riesgo de NC y detección de anomalías.
    """
    from audits.risk_predictor import predict_non_conformity_risk
    from audits.anomaly_detector import detect_anomalies
    from standards.models import Standard

    standards = Standard.objects.filter(is_active=True)
    selected_standard_id = request.GET.get('standard_id')
    try:
        selected_standard_id = int(selected_standard_id) if selected_standard_id else None
    except (ValueError, TypeError):
        selected_standard_id = None

    # Predicciones de riesgo
    prediction_result = predict_non_conformity_risk(
        standard_id=selected_standard_id
    )
    predictions = prediction_result.get('predictions', [])
    prediction_summary = prediction_result.get('summary', {})
    model_info = prediction_result.get('model_info', {})

    # Detección de anomalías
    anomaly_result = detect_anomalies(standard_id=selected_standard_id)
    anomalies = anomaly_result.get('anomalies', [])
    anomaly_summary = anomaly_result.get('summary', {})
    anomaly_thresholds = anomaly_result.get('model_info', {}).get(
        'thresholds', {}
    )

    return render(request, 'mistemplates/demo/f6_05_analitica.html', {
        'standards': standards,
        'selected_standard_id': selected_standard_id,
        'predictions': predictions,
        'prediction_summary': prediction_summary,
        'model_info': model_info,
        'anomalies': anomalies,
        'anomaly_summary': anomaly_summary,
        'anomaly_thresholds': anomaly_thresholds,
    })