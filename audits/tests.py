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