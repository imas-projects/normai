from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import json
from datetime import date, time

from audits.models import (
    AuditProgramHeader, AnnualProgram, AnnualPlan,
    ProcessRequirement, AuditedEvaluationQuestion, Checklist
)
from standards.models import Standard, Clause, StandardRequirement
from processes.models import Process
from company.models import Area, Position


class GapAnalysisTestCase(TestCase):
    """
    Tests para el endpoint get_gap_analysis.
    Valida que la lógica de detección de brechas clasifica correctamente
    los cuatro tipos de estado: COMPLIANT, NON_COMPLIANT,
    INSUFFICIENT_EVIDENCE y NOT_EVALUATED.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='auditor_test',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='auditor_test', password='testpass123')

        self.area = Area.objects.create(name='Área de Prueba')
        self.position = Position.objects.create(
            name='Posición de Prueba',
            code='POS-001',
            area=self.area,
        )
        self.process = Process.objects.create(
            name='Proceso de Prueba',
            objective='Objetivo de prueba',
            creation_date=date(2025, 1, 1),
            process_code='PT-001',
            responsible=self.position,
        )

        self.standard = Standard.objects.create(
            name='ISO 9001:2015 Test',
            version='2015',
            sector='General',
            is_active=True,
        )
        self.clause = Clause.objects.create(
            standard=self.standard,
            code='4.1',
            title='Comprensión del contexto',
            ordering=1,
        )
        self.req1 = StandardRequirement.objects.create(
            clause=self.clause,
            text='Requisito de prueba 1',
            mandatory=True,
            criticality_level='high',
            is_extension=False,
            ordering=1,
        )
        self.req2 = StandardRequirement.objects.create(
            clause=self.clause,
            text='Requisito de prueba 2',
            mandatory=True,
            criticality_level='medium',
            is_extension=False,
            ordering=2,
        )
        self.req3 = StandardRequirement.objects.create(
            clause=self.clause,
            text='Requisito de prueba 3',
            mandatory=False,
            criticality_level='low',
            is_extension=False,
            ordering=3,
        )
        self.req4 = StandardRequirement.objects.create(
            clause=self.clause,
            text='Requisito de prueba 4 sin evaluar',
            mandatory=True,
            criticality_level='high',
            is_extension=False,
            ordering=4,
        )

        self.pr1 = ProcessRequirement.objects.create(
            process=self.process,
            requirement=self.req1,
        )
        self.pr2 = ProcessRequirement.objects.create(
            process=self.process,
            requirement=self.req2,
        )
        self.pr3 = ProcessRequirement.objects.create(
            process=self.process,
            requirement=self.req3,
        )
        self.pr4 = ProcessRequirement.objects.create(
            process=self.process,
            requirement=self.req4,
        )

        self.header = AuditProgramHeader.objects.create(
            year=2025,
            objective='Objetivo de prueba',
            scope='Alcance de prueba',
            audit_criteria='ISO 9001:2015',
            security_standards='Normas de seguridad',
        )
        self.programa = AnnualProgram.objects.create(
            program_header=self.header,
            process=self.process,
            month=5,
            standard=self.standard,
        )
        self.plan = AnnualPlan.objects.create(
            annual_program=self.programa,
            audit_opening_date=date(2025, 5, 1),
            audit_opening_time=time(9, 0),
            audit_opening_location='Sala A',
            audit_closing_date=date(2025, 5, 2),
            audit_closing_time=time(17, 0),
            audit_closing_location='Sala A',
        )

        self.q1 = AuditedEvaluationQuestion.objects.create(
            requirement=self.pr1,
            question_text='[4.1] ¿Cumple el requisito 1?',
        )
        self.q2 = AuditedEvaluationQuestion.objects.create(
            requirement=self.pr2,
            question_text='[4.1] ¿Cumple el requisito 2?',
        )
        self.q3 = AuditedEvaluationQuestion.objects.create(
            requirement=self.pr3,
            question_text='[4.1] ¿Cumple el requisito 3?',
        )

        Checklist.objects.create(
            audit_plan=self.plan, question=self.q1, orden=1,
            compliance=True, evidence='Documentación verificada.'
        )
        Checklist.objects.create(
            audit_plan=self.plan, question=self.q2, orden=2,
            compliance=False, evidence='No se encontró registro.'
        )
        Checklist.objects.create(
            audit_plan=self.plan, question=self.q3, orden=3,
            compliance=False, evidence=''
        )

    def test_gap_analysis_requiere_autenticacion(self):
        """Un usuario no autenticado no puede acceder al endpoint."""
        client_anonimo = Client()
        url = reverse('audits:get_gap_analysis', args=[self.plan.id])
        response = client_anonimo.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_gap_analysis_plan_no_existe(self):
        """El endpoint devuelve 404 si el plan no existe."""
        url = reverse('audits:get_gap_analysis', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('error', data)

    def test_gap_analysis_devuelve_200(self):
        """El endpoint devuelve 200 para un plan válido."""
        url = reverse('audits:get_gap_analysis', args=[self.plan.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_gap_analysis_estructura_respuesta(self):
        """La respuesta contiene las claves esperadas."""
        url = reverse('audits:get_gap_analysis', args=[self.plan.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('summary', data)
        self.assertIn('gaps', data)
        self.assertIn('process', data)
        self.assertIn('standard', data)

    def test_gap_analysis_resumen_correcto(self):
        """El resumen cuenta correctamente cada tipo de brecha."""
        url = reverse('audits:get_gap_analysis', args=[self.plan.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        summary = data['summary']
        self.assertEqual(summary['total'], 4)
        self.assertEqual(summary['compliant'], 1)
        self.assertEqual(summary['non_compliant'], 1)
        self.assertEqual(summary['insufficient_evidence'], 1)
        self.assertEqual(summary['not_evaluated'], 1)

    def test_gap_analysis_compliance_rate(self):
        """La tasa de cumplimiento se calcula correctamente."""
        url = reverse('audits:get_gap_analysis', args=[self.plan.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertAlmostEqual(data['summary']['compliance_rate'], 33.3, places=1)

    def test_gap_analysis_clasifica_compliant(self):
        """El requisito con compliance=True se clasifica como COMPLIANT."""
        url = reverse('audits:get_gap_analysis', args=[self.plan.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        gap = next(g for g in data['gaps'] if g['process_requirement_id'] == self.pr1.id)
        self.assertEqual(gap['status'], 'COMPLIANT')
        self.assertTrue(gap['compliance'])

    def test_gap_analysis_clasifica_non_compliant(self):
        """El requisito con compliance=False y evidencia se clasifica como NON_COMPLIANT."""
        url = reverse('audits:get_gap_analysis', args=[self.plan.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        gap = next(g for g in data['gaps'] if g['process_requirement_id'] == self.pr2.id)
        self.assertEqual(gap['status'], 'NON_COMPLIANT')
        self.assertFalse(gap['compliance'])
        self.assertIsNotNone(gap['evidence'])

    def test_gap_analysis_clasifica_insufficient_evidence(self):
        """El requisito con compliance=False y sin evidencia se clasifica como INSUFFICIENT_EVIDENCE."""
        url = reverse('audits:get_gap_analysis', args=[self.plan.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        gap = next(g for g in data['gaps'] if g['process_requirement_id'] == self.pr3.id)
        self.assertEqual(gap['status'], 'INSUFFICIENT_EVIDENCE')

    def test_gap_analysis_clasifica_not_evaluated(self):
        """El requisito sin ítem de checklist se clasifica como NOT_EVALUATED."""
        url = reverse('audits:get_gap_analysis', args=[self.plan.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        gap = next(g for g in data['gaps'] if g['process_requirement_id'] == self.pr4.id)
        self.assertEqual(gap['status'], 'NOT_EVALUATED')
        self.assertIsNone(gap['checklist_item_id'])

    def test_gap_analysis_trazabilidad_normativa(self):
        """Cada brecha incluye información de requisito, cláusula y norma."""
        url = reverse('audits:get_gap_analysis', args=[self.plan.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        gap = data['gaps'][0]
        self.assertIn('requirement', gap)
        self.assertIn('clause', gap)
        self.assertIn('standard', gap)
        self.assertIn('text', gap['requirement'])
        self.assertIn('criticality_level', gap['requirement'])
        self.assertIn('code', gap['clause'])
        self.assertIn('name', gap['standard'])

    def test_gap_analysis_sin_norma_en_programa(self):
        """El endpoint devuelve error si el programa no tiene norma seleccionada."""
        programa_sin_norma = AnnualProgram.objects.create(
            program_header=self.header,
            process=self.process,
            month=6,
            standard=None,
        )
        plan_sin_norma = AnnualPlan.objects.create(
            annual_program=programa_sin_norma,
            audit_opening_date=date(2025, 6, 1),
            audit_opening_time=time(9, 0),
            audit_opening_location='Sala B',
            audit_closing_date=date(2025, 6, 2),
            audit_closing_time=time(17, 0),
            audit_closing_location='Sala B',
        )
        url = reverse('audits:get_gap_analysis', args=[plan_sin_norma.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertIn('error', data)


class GenerateDynamicChecklistTestCase(TestCase):
    """
    Tests para el endpoint generate_dynamic_checklist.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='auditor_test2',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='auditor_test2', password='testpass123')

        self.area = Area.objects.create(name='Área de Prueba 2')
        self.position = Position.objects.create(
            name='Posición de Prueba 2',
            code='POS-002',
            area=self.area,
        )
        self.process = Process.objects.create(
            name='Proceso de Prueba 2',
            objective='Objetivo de prueba 2',
            creation_date=date(2025, 1, 1),
            process_code='PT-002',
            responsible=self.position,
        )

        self.standard = Standard.objects.create(
            name='ISO 9001:2015 Test 2',
            version='2015',
            sector='General',
            is_active=True,
        )
        self.clause = Clause.objects.create(
            standard=self.standard,
            code='8.5',
            title='Producción y provisión del servicio',
            ordering=1,
        )
        self.req1 = StandardRequirement.objects.create(
            clause=self.clause,
            text='Requisito producción 1',
            mandatory=True,
            criticality_level='high',
            is_extension=False,
            ordering=1,
        )
        self.req2 = StandardRequirement.objects.create(
            clause=self.clause,
            text='Requisito producción 2',
            mandatory=True,
            criticality_level='medium',
            is_extension=False,
            ordering=2,
        )

        ProcessRequirement.objects.create(
            process=self.process,
            requirement=self.req1,
        )
        ProcessRequirement.objects.create(
            process=self.process,
            requirement=self.req2,
        )

        self.header = AuditProgramHeader.objects.create(
            year=2025,
            objective='Objetivo test 2',
            scope='Alcance test 2',
            audit_criteria='ISO 9001:2015',
            security_standards='Normas de seguridad',
        )
        self.programa = AnnualProgram.objects.create(
            program_header=self.header,
            process=self.process,
            month=6,
            standard=self.standard,
        )
        self.plan = AnnualPlan.objects.create(
            annual_program=self.programa,
            audit_opening_date=date(2025, 6, 1),
            audit_opening_time=time(9, 0),
            audit_opening_location='Sala A',
            audit_closing_date=date(2025, 6, 2),
            audit_closing_time=time(17, 0),
            audit_closing_location='Sala A',
        )

    def _post(self, annual_plan_id):
        url = reverse('audits:generate_dynamic_checklist')
        return self.client.post(
            url,
            data=json.dumps({'annual_plan_id': annual_plan_id}),
            content_type='application/json',
        )

    def test_generate_requiere_autenticacion(self):
        """Un usuario no autenticado no puede generar el checklist."""
        client_anonimo = Client()
        url = reverse('audits:generate_dynamic_checklist')
        response = client_anonimo.post(
            url,
            data=json.dumps({'annual_plan_id': self.plan.id}),
            content_type='application/json',
        )
        self.assertNotEqual(response.status_code, 200)

    def test_generate_solo_acepta_post(self):
        """El endpoint rechaza peticiones GET con 405."""
        url = reverse('audits:generate_dynamic_checklist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_generate_crea_checklist(self):
        """La generación crea el número correcto de ítems de checklist."""
        response = self._post(self.plan.id)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['total_items'], 2)
        self.assertEqual(Checklist.objects.filter(audit_plan=self.plan).count(), 2)

    def test_generate_crea_preguntas_vinculadas(self):
        """Las preguntas generadas están vinculadas a ProcessRequirement."""
        self._post(self.plan.id)
        preguntas = AuditedEvaluationQuestion.objects.filter(
            requirement__process=self.process
        )
        self.assertEqual(preguntas.count(), 2)
        for pregunta in preguntas:
            self.assertIsNotNone(pregunta.requirement)
            self.assertIsNotNone(pregunta.standard_requirement)

    def test_generate_no_duplica_checklist(self):
        """El endpoint rechaza la generación si ya existe un checklist."""
        self._post(self.plan.id)
        response = self._post(self.plan.id)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(Checklist.objects.filter(audit_plan=self.plan).count(), 2)

    def test_generate_sin_norma_devuelve_error(self):
        """El endpoint devuelve error si el programa no tiene norma."""
        programa_sin_norma = AnnualProgram.objects.create(
            program_header=self.header,
            process=self.process,
            month=7,
            standard=None,
        )
        plan_sin_norma = AnnualPlan.objects.create(
            annual_program=programa_sin_norma,
            audit_opening_date=date(2025, 7, 1),
            audit_opening_time=time(9, 0),
            audit_opening_location='Sala C',
            audit_closing_date=date(2025, 7, 2),
            audit_closing_time=time(17, 0),
            audit_closing_location='Sala C',
        )
        response = self._post(plan_sin_norma.id)
        data = json.loads(response.content)
        self.assertIn('error', data)

    def test_generate_texto_pregunta_incluye_clausula(self):
        """El texto de las preguntas generadas incluye el código de cláusula."""
        self._post(self.plan.id)
        preguntas = AuditedEvaluationQuestion.objects.filter(
            requirement__process=self.process
        )
        for pregunta in preguntas:
            self.assertIn('[8.5]', pregunta.question_text)

    def test_generate_plan_no_existe(self):
        """El endpoint devuelve error si el plan no existe."""
        response = self._post(99999)
        data = json.loads(response.content)
        self.assertIn('error', data)

class ComplianceEngineTestCase(TestCase):
    """
    Tests para el motor de cumplimiento — F3-02 y F3-03.
    Cubre: cálculo por proceso, agregado por norma, persistencia,
    overwrite, penalización por hallazgos, comparación temporal
    e histórico con limit.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='auditor_compliance',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='auditor_compliance', password='testpass123')

        self.area = Area.objects.create(name='Área Compliance')
        self.position = Position.objects.create(
            name='Posición Compliance',
            code='POS-003',
            area=self.area,
        )
        self.process = Process.objects.create(
            name='Proceso Compliance Test',
            objective='Objetivo compliance',
            creation_date=date(2025, 1, 1),
            process_code='PC-001',
            responsible=self.position,
        )
        self.standard = Standard.objects.create(
            name='ISO Test Compliance',
            version='2015',
            sector='General',
            is_active=True,
        )
        self.clause = Clause.objects.create(
            standard=self.standard,
            code='4.1',
            title='Cláusula de prueba',
            ordering=1,
        )
        # Requisito high mandatory — peso 3
        self.req_high = StandardRequirement.objects.create(
            clause=self.clause,
            text='Requisito alto obligatorio',
            mandatory=True,
            criticality_level='high',
            is_extension=False,
            ordering=1,
        )
        # Requisito medium mandatory — peso 2
        self.req_medium = StandardRequirement.objects.create(
            clause=self.clause,
            text='Requisito medio obligatorio',
            mandatory=True,
            criticality_level='medium',
            is_extension=False,
            ordering=2,
        )

        self.pr_high = ProcessRequirement.objects.create(
            process=self.process,
            requirement=self.req_high,
        )
        self.pr_medium = ProcessRequirement.objects.create(
            process=self.process,
            requirement=self.req_medium,
        )

        self.header = AuditProgramHeader.objects.create(
            year=2025,
            objective='Objetivo test compliance',
            scope='Alcance test',
            audit_criteria='ISO Test',
            security_standards='Normas',
        )
        self.programa = AnnualProgram.objects.create(
            program_header=self.header,
            process=self.process,
            month=1,
            standard=self.standard,
        )
        self.plan = AnnualPlan.objects.create(
            annual_program=self.programa,
            audit_opening_date=date(2025, 1, 1),
            audit_opening_time=time(9, 0),
            audit_opening_location='Sala A',
            audit_closing_date=date(2025, 1, 2),
            audit_closing_time=time(17, 0),
            audit_closing_location='Sala A',
        )

        # Preguntas vinculadas a los ProcessRequirements
        self.q_high = AuditedEvaluationQuestion.objects.create(
            requirement=self.pr_high,
            question_text='[4.1] ¿Cumple req alto?',
        )
        self.q_medium = AuditedEvaluationQuestion.objects.create(
            requirement=self.pr_medium,
            question_text='[4.1] ¿Cumple req medio?',
        )

    def _create_checklist(self, plan, compliance_high, evidence_high,
                          compliance_medium, evidence_medium):
        """Helper para crear checklist items en un plan."""
        Checklist.objects.create(
            audit_plan=plan, question=self.q_high, orden=1,
            compliance=compliance_high, evidence=evidence_high,
        )
        Checklist.objects.create(
            audit_plan=plan, question=self.q_medium, orden=2,
            compliance=compliance_medium, evidence=evidence_medium,
        )

    def _create_plan(self, month):
        """Helper para crear un AnnualPlan adicional."""
        return AnnualPlan.objects.create(
            annual_program=self.programa,
            audit_opening_date=date(2025, month, 1),
            audit_opening_time=time(9, 0),
            audit_opening_location='Sala A',
            audit_closing_date=date(2025, month, 2),
            audit_closing_time=time(17, 0),
            audit_closing_location='Sala A',
        )

    # ─── Cálculo por proceso ───────────────────────────────────────────

    def test_calculo_proceso_ambos_conformes(self):
        """Dos requisitos conformes → score 1.0 EXCELLENT."""
        self._create_checklist(
            self.plan,
            True, 'Evidencia A',
            True, 'Evidencia B',
        )
        from audits.compliance_engine import calculate_compliance_for_plan
        result = calculate_compliance_for_plan(self.plan.id)
        self.assertTrue(result['success'])
        snapshot = result['snapshot']
        self.assertAlmostEqual(snapshot['score'], 100.0, places=1)
        self.assertEqual(snapshot['category'], 'EXCELLENT')
        self.assertEqual(snapshot['compliant_count'], 2)

    def test_calculo_proceso_ninguno_conforme(self):
        """Dos requisitos no conformes → score 0.0 CRITICAL."""
        self._create_checklist(
            self.plan,
            False, 'No cumple A',
            False, 'No cumple B',
        )
        from audits.compliance_engine import calculate_compliance_for_plan
        result = calculate_compliance_for_plan(self.plan.id)
        snapshot = result['snapshot']
        self.assertAlmostEqual(snapshot['score'], 0.0, places=1)
        self.assertEqual(snapshot['category'], 'CRITICAL')
        self.assertEqual(snapshot['non_compliant_count'], 2)

    def test_calculo_proceso_ponderacion_por_peso(self):
        """
        req_high (peso 3) COMPLIANT, req_medium (peso 2) NON_COMPLIANT.
        score = (1.0×3 + 0.0×2) / (3+2) = 3/5 = 0.6 → PARTIAL
        """
        self._create_checklist(
            self.plan,
            True, 'Evidencia ok',
            False, 'No cumple',
        )
        from audits.compliance_engine import calculate_compliance_for_plan
        result = calculate_compliance_for_plan(self.plan.id)
        snapshot = result['snapshot']
        self.assertAlmostEqual(snapshot['score'], 60.0, places=1)
        self.assertEqual(snapshot['category'], 'PARTIAL')

    def test_calculo_proceso_insufficient_evidence(self):
        """
        req_high INSUFFICIENT_EVIDENCE (0.25, peso 3),
        req_medium COMPLIANT (1.0, peso 2).
        score = (0.25×3 + 1.0×2) / 5 = 2.75/5 = 0.55 → PARTIAL
        """
        self._create_checklist(
            self.plan,
            False, '',
            True, 'Evidencia ok',
        )
        from audits.compliance_engine import calculate_compliance_for_plan
        result = calculate_compliance_for_plan(self.plan.id)
        snapshot = result['snapshot']
        self.assertAlmostEqual(snapshot['score'], 55.0, places=1)
        self.assertEqual(snapshot['category'], 'PARTIAL')

    # ─── Persistencia y overwrite ──────────────────────────────────────

    def test_persistencia_snapshot(self):
        """El snapshot se persiste en base de datos."""
        self._create_checklist(self.plan, True, 'E', True, 'E')
        from audits.compliance_engine import calculate_compliance_for_plan
        from audits.models import ComplianceSnapshot
        calculate_compliance_for_plan(self.plan.id)
        self.assertEqual(
            ComplianceSnapshot.objects.filter(annual_plan=self.plan).count(), 1
        )

    def test_no_duplica_sin_overwrite(self):
        """Sin overwrite, el segundo cálculo devuelve error."""
        self._create_checklist(self.plan, True, 'E', True, 'E')
        from audits.compliance_engine import calculate_compliance_for_plan
        calculate_compliance_for_plan(self.plan.id)
        result = calculate_compliance_for_plan(self.plan.id)
        self.assertIn('error', result)

    def test_overwrite_recalcula(self):
        """Con overwrite=True, el snapshot se recalcula."""
        self._create_checklist(self.plan, True, 'E', True, 'E')
        from audits.compliance_engine import calculate_compliance_for_plan
        from audits.models import ComplianceSnapshot
        calculate_compliance_for_plan(self.plan.id)
        result = calculate_compliance_for_plan(self.plan.id, overwrite=True)
        self.assertTrue(result['success'])
        self.assertEqual(
            ComplianceSnapshot.objects.filter(annual_plan=self.plan).count(), 1
        )

    def test_trazabilidad_detail(self):
        """El campo detail incluye desglose por requisito."""
        self._create_checklist(self.plan, True, 'E', False, 'No cumple')
        from audits.compliance_engine import calculate_compliance_for_plan
        result = calculate_compliance_for_plan(self.plan.id)
        detail = result['snapshot']['detail']
        self.assertEqual(len(detail), 2)
        for item in detail:
            self.assertIn('process_requirement_id', item)
            self.assertIn('status', item)
            self.assertIn('final_score', item)
            self.assertIn('weight', item)
            self.assertIn('clause_code', item)

    # ─── Penalización por hallazgos ────────────────────────────────────

    def test_penalizacion_nc_mayor(self):
        """
        req_high COMPLIANT (1.0) con NC_MAYOR (-0.3) → final_score 0.7
        req_medium COMPLIANT (1.0) sin hallazgo → final_score 1.0
        score = (0.7×3 + 1.0×2) / 5 = 4.1/5 = 0.82 → GOOD
        """
        self._create_checklist(self.plan, True, 'E', True, 'E')
        from audits.models import Findings
        Findings.objects.create(
            audit_plan=self.plan,
            requirement=self.pr_high,
            finding_text='No conformidad mayor detectada',
            classification='NC_MAYOR',
        )
        from audits.compliance_engine import calculate_compliance_for_plan
        result = calculate_compliance_for_plan(self.plan.id)
        snapshot = result['snapshot']
        self.assertAlmostEqual(snapshot['score'], 82.0, places=1)
        self.assertEqual(snapshot['category'], 'GOOD')

    def test_penalizacion_nc_menor(self):
        """
        req_high COMPLIANT (1.0) con NC_MENOR (-0.15) → final_score 0.85
        req_medium COMPLIANT (1.0) sin hallazgo → final_score 1.0
        score = (0.85×3 + 1.0×2) / 5 = 4.55/5 = 0.91 → EXCELLENT
        """
        self._create_checklist(self.plan, True, 'E', True, 'E')
        from audits.models import Findings
        Findings.objects.create(
            audit_plan=self.plan,
            requirement=self.pr_high,
            finding_text='No conformidad menor detectada',
            classification='NC_MENOR',
        )
        from audits.compliance_engine import calculate_compliance_for_plan
        result = calculate_compliance_for_plan(self.plan.id)
        snapshot = result['snapshot']
        self.assertAlmostEqual(snapshot['score'], 91.0, places=1)
        self.assertEqual(snapshot['category'], 'EXCELLENT')

    # ─── Agregado por norma ────────────────────────────────────────────

    def test_agregado_por_norma(self):
        """El agregado por norma devuelve el score global correctamente."""
        self._create_checklist(self.plan, True, 'E', True, 'E')
        from audits.compliance_engine import (
            calculate_compliance_for_plan, get_compliance_by_standard
        )
        calculate_compliance_for_plan(self.plan.id)
        result = get_compliance_by_standard(self.standard.id)
        self.assertTrue(result['success'])
        self.assertAlmostEqual(result['global_score'], 100.0, places=1)
        self.assertEqual(result['global_category'], 'EXCELLENT')
        self.assertEqual(result['total_processes'], 1)

    def test_agregado_sin_snapshots(self):
        """Sin snapshots, get_compliance_by_standard devuelve error."""
        from audits.compliance_engine import get_compliance_by_standard
        result = get_compliance_by_standard(self.standard.id)
        self.assertIn('error', result)

    # ─── Comparación temporal ──────────────────────────────────────────

    def test_comparacion_temporal(self):
        """Compara dos snapshots e identifica mejoras correctamente."""
        # Plan 1: req_high NON_COMPLIANT, req_medium NON_COMPLIANT
        self._create_checklist(
            self.plan, False, 'No cumple', False, 'No cumple'
        )
        from audits.compliance_engine import (
            calculate_compliance_for_plan, compare_compliance_periods
        )
        result_a = calculate_compliance_for_plan(self.plan.id)
        snapshot_id_a = result_a['snapshot']['id']

        # Plan 2: ambos COMPLIANT
        plan2 = self._create_plan(month=6)
        q_high2 = AuditedEvaluationQuestion.objects.create(
            requirement=self.pr_high,
            question_text='[4.1] ¿Cumple req alto? P2',
        )
        q_medium2 = AuditedEvaluationQuestion.objects.create(
            requirement=self.pr_medium,
            question_text='[4.1] ¿Cumple req medio? P2',
        )
        Checklist.objects.create(
            audit_plan=plan2, question=q_high2, orden=1,
            compliance=True, evidence='Evidencia ok',
        )
        Checklist.objects.create(
            audit_plan=plan2, question=q_medium2, orden=2,
            compliance=True, evidence='Evidencia ok',
        )
        result_b = calculate_compliance_for_plan(plan2.id)
        snapshot_id_b = result_b['snapshot']['id']

        result = compare_compliance_periods(snapshot_id_a, snapshot_id_b)
        self.assertTrue(result['success'])
        self.assertAlmostEqual(result['summary']['score_delta'], 100.0, places=1)
        self.assertEqual(result['summary']['improved_requirements'], 2)
        self.assertEqual(result['summary']['declined_requirements'], 0)

    def test_comparacion_procesos_distintos_da_error(self):
        """No se pueden comparar snapshots de procesos diferentes."""
        from audits.models import ComplianceSnapshot
        from audits.compliance_engine import compare_compliance_periods

        proceso2 = Process.objects.create(
            name='Proceso 2',
            objective='Obj',
            creation_date=date(2025, 1, 1),
            process_code='PC-002',
            responsible=self.position,
        )
        snap_a = ComplianceSnapshot.objects.create(
            annual_plan=self.plan,
            process=self.process,
            standard=self.standard,
            score=0.5, category='PARTIAL',
            total_requirements=2, compliant_count=1,
            non_compliant_count=1, insufficient_count=0,
            not_evaluated_count=0, detail=[],
        )
        snap_b = ComplianceSnapshot.objects.create(
            annual_plan=self.plan,
            process=proceso2,
            standard=self.standard,
            score=0.8, category='GOOD',
            total_requirements=2, compliant_count=2,
            non_compliant_count=0, insufficient_count=0,
            not_evaluated_count=0, detail=[],
        )
        result = compare_compliance_periods(snap_a.id, snap_b.id)
        self.assertIn('error', result)

    # ─── Histórico con limit ───────────────────────────────────────────

    def test_historico_limit_devuelve_mas_recientes(self):
        """Con limit=2 y 3 snapshots, devuelve los 2 más recientes."""
        from audits.models import ComplianceSnapshot
        from audits.compliance_engine import get_compliance_history
        

        # Crear 3 snapshots con scores distintos
        plan1 = self._create_plan(month=2)
        plan2 = self._create_plan(month=3)
        plan3 = self._create_plan(month=4)

        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()

        snap1 = ComplianceSnapshot.objects.create(
            annual_plan=plan1, process=self.process, standard=self.standard,
            score=0.2, category='CRITICAL', total_requirements=2,
            compliant_count=0, non_compliant_count=2,
            insufficient_count=0, not_evaluated_count=0, detail=[],
        )
        ComplianceSnapshot.objects.filter(pk=snap1.pk).update(
            calculated_at=now - timedelta(days=60)
        )

        snap2 = ComplianceSnapshot.objects.create(
            annual_plan=plan2, process=self.process, standard=self.standard,
            score=0.5, category='PARTIAL', total_requirements=2,
            compliant_count=1, non_compliant_count=1,
            insufficient_count=0, not_evaluated_count=0, detail=[],
        )
        ComplianceSnapshot.objects.filter(pk=snap2.pk).update(
            calculated_at=now - timedelta(days=30)
        )

        snap3 = ComplianceSnapshot.objects.create(
            annual_plan=plan3, process=self.process, standard=self.standard,
            score=0.9, category='EXCELLENT', total_requirements=2,
            compliant_count=2, non_compliant_count=0,
            insufficient_count=0, not_evaluated_count=0, detail=[],
        )
        ComplianceSnapshot.objects.filter(pk=snap3.pk).update(
            calculated_at=now
        )

        result = get_compliance_history(
            self.process.id, self.standard.id, limit=2
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['total_snapshots'], 2)

        # Deben ser los 2 más recientes (snap2 y snap3)
        scores = [h['score'] for h in result['history']]
        self.assertIn(50.0, scores)
        self.assertIn(90.0, scores)
        self.assertNotIn(20.0, scores)

        # Orden cronológico: snap2 antes que snap3
        self.assertLess(
            result['history'][0]['score'],
            result['history'][1]['score']
        )

    def test_historico_tendencia_usa_estado_actual(self):
        """La tendencia se calcula con el snapshot más reciente disponible."""
        from audits.models import ComplianceSnapshot
        from audits.compliance_engine import get_compliance_history

        plan1 = self._create_plan(month=2)
        plan2 = self._create_plan(month=3)

        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()

        snap_old = ComplianceSnapshot.objects.create(
            annual_plan=plan1, process=self.process, standard=self.standard,
            score=0.3, category='LOW', total_requirements=2,
            compliant_count=0, non_compliant_count=2,
            insufficient_count=0, not_evaluated_count=0, detail=[],
        )
        ComplianceSnapshot.objects.filter(pk=snap_old.pk).update(
            calculated_at=now - timedelta(days=30)
        )

        snap_new = ComplianceSnapshot.objects.create(
            annual_plan=plan2, process=self.process, standard=self.standard,
            score=0.9, category='EXCELLENT', total_requirements=2,
            compliant_count=2, non_compliant_count=0,
            insufficient_count=0, not_evaluated_count=0, detail=[],
        )
        ComplianceSnapshot.objects.filter(pk=snap_new.pk).update(
            calculated_at=now
        )

        result = get_compliance_history(self.process.id, self.standard.id)
        self.assertEqual(result['trend'], 'IMPROVING')