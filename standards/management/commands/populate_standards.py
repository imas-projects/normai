from django.core.management.base import BaseCommand
from standards.models import Standard, Clause, StandardRequirement, StandardMapping


class Command(BaseCommand):
    help = 'Carga los datos iniciales de ISO 9001:2015 y AS9100 Rev D'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando carga de datos normativos...')

        if Standard.objects.exists():
            self.stdout.write(self.style.WARNING(
                'Ya existen normas en la base de datos. '
                'Ejecuta este comando solo en una base de datos limpia.'
            ))
            return

        iso = self._create_iso9001()
        as9100 = self._create_as9100()
        self._create_mappings(iso, as9100)

        self.stdout.write(self.style.SUCCESS('Carga completada correctamente.'))
        self.stdout.write(f'  ISO 9001 clausulas: {Clause.objects.filter(standard=iso).count()}')
        self.stdout.write(f'  ISO 9001 requisitos: {StandardRequirement.objects.filter(clause__standard=iso).count()}')
        self.stdout.write(f'  AS9100 clausulas: {Clause.objects.filter(standard=as9100).count()}')
        self.stdout.write(f'  AS9100 requisitos: {StandardRequirement.objects.filter(clause__standard=as9100).count()}')
        self.stdout.write(f'  Mapeos creados: {StandardMapping.objects.count()}')

    # ─────────────────────────────────────────────
    # ISO 9001:2015
    # ─────────────────────────────────────────────

    def _create_iso9001(self):
        iso = Standard.objects.create(
            name='ISO 9001:2015',
            version='2015',
            sector='General',
            is_active=True,
        )
        self.stdout.write('  Creando ISO 9001:2015...')

        data = [
            # (code, title, parent_code, ordering, requirements)
            ('4', 'Contexto de la organización', None, 1, []),
            ('4.1', 'Comprensión de la organización y de su contexto', '4', 1, [
                ('La organización debe determinar las cuestiones externas e internas que son pertinentes para su propósito y su dirección estratégica, y que afectan a su capacidad para lograr los resultados previstos de su sistema de gestión de la calidad.', True, 'high'),
                ('La organización debe realizar el seguimiento y la revisión de la información sobre estas cuestiones externas e internas.', True, 'medium'),
            ]),
            ('4.2', 'Comprensión de las necesidades y expectativas de las partes interesadas', '4', 2, [
                ('La organización debe determinar las partes interesadas que son pertinentes al sistema de gestión de la calidad y los requisitos pertinentes de estas partes interesadas.', True, 'high'),
                ('La organización debe realizar el seguimiento y la revisión de la información sobre estas partes interesadas y sus requisitos pertinentes.', True, 'medium'),
            ]),
            ('4.3', 'Determinación del alcance del sistema de gestión de la calidad', '4', 3, [
                ('La organización debe determinar los límites y la aplicabilidad del sistema de gestión de la calidad para establecer su alcance.', True, 'high'),
                ('El alcance debe estar disponible y mantenerse como información documentada.', True, 'high'),
            ]),
            ('4.4', 'Sistema de gestión de la calidad y sus procesos', '4', 4, [
                ('La organización debe establecer, implementar, mantener y mejorar continuamente un sistema de gestión de la calidad, incluidos los procesos necesarios y sus interacciones.', True, 'high'),
                ('La organización debe mantener información documentada para apoyar la operación de sus procesos y conservar información documentada para tener la confianza de que los procesos se realizan según lo planificado.', True, 'high'),
            ]),

            ('5', 'Liderazgo', None, 2, []),
            ('5.1', 'Liderazgo y compromiso', '5', 1, []),
            ('5.1.1', 'Generalidades', '5.1', 1, [
                ('La alta dirección debe demostrar liderazgo y compromiso con respecto al sistema de gestión de la calidad asumiendo la responsabilidad y obligación de rendir cuentas con relación a la eficacia del SGC.', True, 'high'),
                ('La alta dirección debe asegurarse de que se establezcan la política de la calidad y los objetivos de la calidad para el sistema de gestión de la calidad.', True, 'high'),
            ]),
            ('5.1.2', 'Enfoque al cliente', '5.1', 2, [
                ('La alta dirección debe demostrar liderazgo y compromiso con respecto al enfoque al cliente asegurándose de que se determinan, se comprenden y se cumplen regularmente los requisitos del cliente.', True, 'high'),
                ('La alta dirección debe asegurarse de que se mantiene el enfoque en aumentar la satisfacción del cliente.', True, 'medium'),
            ]),
            ('5.2', 'Política', '5', 2, []),
            ('5.2.1', 'Establecimiento de la política de la calidad', '5.2', 1, [
                ('La alta dirección debe establecer, implementar y mantener una política de la calidad que sea apropiada al propósito y contexto de la organización.', True, 'high'),
                ('La política de la calidad debe proporcionar un marco de referencia para el establecimiento de los objetivos de la calidad.', True, 'high'),
            ]),
            ('5.2.2', 'Comunicación de la política de la calidad', '5.2', 2, [
                ('La política de la calidad debe estar disponible y mantenerse como información documentada.', True, 'high'),
                ('La política de la calidad debe comunicarse, entenderse y aplicarse dentro de la organización.', True, 'medium'),
            ]),
            ('5.3', 'Roles, responsabilidades y autoridades en la organización', '5', 3, [
                ('La alta dirección debe asegurarse de que las responsabilidades y autoridades para los roles pertinentes se asignen, se comuniquen y se entiendan en toda la organización.', True, 'high'),
            ]),

            ('6', 'Planificación', None, 3, []),
            ('6.1', 'Acciones para abordar riesgos y oportunidades', '6', 1, []),
            ('6.1.1', 'Generalidades — riesgos y oportunidades', '6.1', 1, [
                ('Al planificar el sistema de gestión de la calidad, la organización debe considerar las cuestiones del contexto y los requisitos de las partes interesadas, y determinar los riesgos y oportunidades que es necesario abordar.', True, 'high'),
            ]),
            ('6.1.2', 'Acciones sobre riesgos y oportunidades', '6.1', 2, [
                ('La organización debe planificar las acciones para abordar estos riesgos y oportunidades, cómo integrar e implementar las acciones en sus procesos del SGC y evaluar la eficacia de estas acciones.', True, 'high'),
            ]),
            ('6.2', 'Objetivos de la calidad y planificación para lograrlos', '6', 2, [
                ('La organización debe establecer objetivos de la calidad para las funciones y niveles pertinentes y los procesos necesarios para el sistema de gestión de la calidad.', True, 'high'),
                ('Los objetivos de la calidad deben ser medibles, tener en cuenta los requisitos aplicables y ser pertinentes para la conformidad de los productos y servicios.', True, 'high'),
                ('La organización debe mantener información documentada sobre los objetivos de la calidad.', True, 'medium'),
            ]),
            ('6.3', 'Planificación de los cambios', '6', 3, [
                ('Cuando la organización determine la necesidad de cambios en el sistema de gestión de la calidad, estos cambios se deben llevar a cabo de manera planificada.', True, 'medium'),
            ]),

            ('7', 'Apoyo', None, 4, []),
            ('7.1', 'Recursos', '7', 1, []),
            ('7.1.1', 'Generalidades — recursos', '7.1', 1, [
                ('La organización debe determinar y proporcionar los recursos necesarios para el establecimiento, implementación, mantenimiento y mejora continua del sistema de gestión de la calidad.', True, 'high'),
            ]),
            ('7.1.2', 'Personas', '7.1', 2, [
                ('La organización debe determinar y proporcionar las personas necesarias para la implementación eficaz de su sistema de gestión de la calidad y para la operación y control de sus procesos.', True, 'high'),
            ]),
            ('7.1.3', 'Infraestructura', '7.1', 3, [
                ('La organización debe determinar, proporcionar y mantener la infraestructura necesaria para la operación de sus procesos y lograr la conformidad de los productos y servicios.', True, 'medium'),
            ]),
            ('7.1.4', 'Ambiente para la operación de los procesos', '7.1', 4, [
                ('La organización debe determinar, proporcionar y mantener el ambiente necesario para la operación de sus procesos y para lograr la conformidad de los productos y servicios.', True, 'medium'),
            ]),
            ('7.1.5', 'Recursos de seguimiento y medición', '7.1', 5, [
                ('La organización debe determinar y proporcionar los recursos necesarios para asegurarse de la validez y fiabilidad de los resultados cuando se realice seguimiento o medición.', True, 'high'),
            ]),
            ('7.1.6', 'Conocimientos de la organización', '7.1', 6, [
                ('La organización debe determinar los conocimientos necesarios para la operación de sus procesos y para lograr la conformidad de los productos y servicios.', True, 'medium'),
            ]),
            ('7.2', 'Competencia', '7', 2, [
                ('La organización debe determinar la competencia necesaria de las personas que realizan, bajo su control, un trabajo que afecta al desempeño y eficacia del SGC.', True, 'high'),
                ('La organización debe asegurarse de que estas personas sean competentes, basándose en la educación, formación o experiencia apropiadas.', True, 'high'),
                ('La organización debe conservar información documentada apropiada como evidencia de la competencia.', True, 'high'),
            ]),
            ('7.3', 'Toma de conciencia', '7', 3, [
                ('La organización debe asegurarse de que las personas que realizan el trabajo bajo el control de la organización tomen conciencia de la política de la calidad y los objetivos de la calidad pertinentes.', True, 'medium'),
            ]),
            ('7.4', 'Comunicación', '7', 4, [
                ('La organización debe determinar las comunicaciones internas y externas pertinentes al sistema de gestión de la calidad.', True, 'medium'),
            ]),
            ('7.5', 'Información documentada', '7', 5, []),
            ('7.5.1', 'Generalidades — información documentada', '7.5', 1, [
                ('El sistema de gestión de la calidad de la organización debe incluir la información documentada requerida por esta Norma Internacional y la determinada por la organización como necesaria para la eficacia del SGC.', True, 'high'),
            ]),
            ('7.5.2', 'Creación y actualización', '7.5', 2, [
                ('Al crear y actualizar la información documentada, la organización debe asegurarse de que sea apropiada la identificación y descripción, el formato y los medios de soporte, y la revisión y aprobación con respecto a la conveniencia y adecuación.', True, 'high'),
            ]),
            ('7.5.3', 'Control de la información documentada', '7.5', 3, [
                ('La información documentada requerida por el sistema de gestión de la calidad y por esta Norma Internacional se debe controlar para asegurarse de que esté disponible y sea idónea para su uso, donde y cuando se necesite.', True, 'high'),
                ('La información documentada de origen externo que la organización determina como necesaria para la planificación y operación del sistema de gestión de la calidad se debe identificar y controlar.', True, 'medium'),
            ]),

            ('8', 'Operación', None, 5, []),
            ('8.1', 'Planificación y control operacional', '8', 1, [
                ('La organización debe planificar, implementar, controlar, hacer seguimiento y revisar los procesos necesarios para cumplir los requisitos para la provisión de productos y servicios.', True, 'high'),
                ('La organización debe conservar información documentada en la medida necesaria para tener confianza en que los procesos se han llevado a cabo según lo planificado.', True, 'high'),
            ]),
            ('8.2', 'Requisitos para los productos y servicios', '8', 2, []),
            ('8.2.1', 'Comunicación con el cliente', '8.2', 1, [
                ('La comunicación con los clientes debe incluir proporcionar la información relativa a los productos y servicios, tratar las consultas y los contratos o pedidos, incluyendo los cambios.', True, 'medium'),
            ]),
            ('8.2.2', 'Determinación de los requisitos para productos y servicios', '8.2', 2, [
                ('La organización debe asegurarse de que tiene la capacidad de cumplir los requisitos para los productos y servicios que se van a ofrecer a los clientes.', True, 'high'),
            ]),
            ('8.2.3', 'Revisión de los requisitos para productos y servicios', '8.2', 3, [
                ('La organización debe asegurarse de que tiene la capacidad de cumplir los requisitos para los productos y servicios que se van a ofrecer a los clientes antes de comprometerse a suministrar productos y servicios.', True, 'high'),
                ('La organización debe conservar información documentada sobre los resultados de la revisión.', True, 'high'),
            ]),
            ('8.2.4', 'Cambios en los requisitos para productos y servicios', '8.2', 4, [
                ('La organización debe asegurarse de que la información documentada pertinente sea modificada, y de que las personas pertinentes sean conscientes de los requisitos modificados, cuando se cambien los requisitos para los productos y servicios.', True, 'medium'),
            ]),
            ('8.3', 'Diseño y desarrollo de los productos y servicios', '8', 3, []),
            ('8.3.1', 'Generalidades — diseño y desarrollo', '8.3', 1, [
                ('La organización debe establecer, implementar y mantener un proceso de diseño y desarrollo que sea adecuado para asegurarse de la posterior provisión de productos y servicios.', True, 'high'),
            ]),
            ('8.3.2', 'Planificación del diseño y desarrollo', '8.3', 2, [
                ('Al determinar las etapas y controles para el diseño y desarrollo, la organización debe considerar la naturaleza, duración y complejidad de las actividades de diseño y desarrollo.', True, 'high'),
            ]),
            ('8.3.3', 'Entradas para el diseño y desarrollo', '8.3', 3, [
                ('La organización debe determinar los requisitos esenciales para los tipos específicos de productos y servicios a diseñar y desarrollar.', True, 'high'),
            ]),
            ('8.3.4', 'Controles del diseño y desarrollo', '8.3', 4, [
                ('La organización debe aplicar controles al proceso de diseño y desarrollo para asegurarse de que se definen los resultados a lograr.', True, 'high'),
            ]),
            ('8.3.5', 'Salidas del diseño y desarrollo', '8.3', 5, [
                ('La organización debe asegurarse de que las salidas del diseño y desarrollo cumplen los requisitos de las entradas, son adecuadas para los procesos posteriores de provisión de productos y servicios.', True, 'high'),
            ]),
            ('8.3.6', 'Cambios del diseño y desarrollo', '8.3', 6, [
                ('La organización debe identificar, revisar y controlar los cambios hechos durante el diseño y desarrollo de los productos y servicios.', True, 'high'),
            ]),
            ('8.4', 'Control de los procesos, productos y servicios suministrados externamente', '8', 4, []),
            ('8.4.1', 'Generalidades — control externo', '8.4', 1, [
                ('La organización debe asegurarse de que los procesos, productos y servicios suministrados externamente son conformes a los requisitos especificados.', True, 'high'),
            ]),
            ('8.4.2', 'Tipo y alcance del control', '8.4', 2, [
                ('La organización debe asegurarse de que los procesos, productos y servicios suministrados externamente no afectan de manera adversa a la capacidad de la organización de entregar productos y servicios conformes.', True, 'high'),
            ]),
            ('8.4.3', 'Información para los proveedores externos', '8.4', 3, [
                ('La organización debe comunicar a los proveedores externos sus requisitos para los procesos, productos y servicios a proporcionar.', True, 'medium'),
            ]),
            ('8.5', 'Producción y provisión del servicio', '8', 5, []),
            ('8.5.1', 'Control de la producción y de la provisión del servicio', '8.5', 1, [
                ('La organización debe implementar la producción y provisión del servicio bajo condiciones controladas.', True, 'high'),
                ('Las condiciones controladas deben incluir la disponibilidad de información documentada que defina las características de los productos a producir o los servicios a prestar.', True, 'high'),
            ]),
            ('8.5.2', 'Identificación y trazabilidad', '8.5', 2, [
                ('La organización debe utilizar los medios apropiados para identificar las salidas cuando sea necesario para asegurar la conformidad de los productos y servicios.', True, 'high'),
                ('La organización debe controlar la identificación única de las salidas cuando la trazabilidad sea un requisito, y debe conservar la información documentada necesaria para permitir la trazabilidad.', True, 'high'),
            ]),
            ('8.5.3', 'Propiedad perteneciente a los clientes o proveedores externos', '8.5', 3, [
                ('La organización debe cuidar la propiedad perteneciente a los clientes o a proveedores externos mientras esté bajo el control de la organización o esté siendo utilizada por la misma.', True, 'medium'),
            ]),
            ('8.5.4', 'Preservación', '8.5', 4, [
                ('La organización debe preservar las salidas durante la producción y prestación del servicio, en la medida necesaria para asegurarse de la conformidad con los requisitos.', True, 'medium'),
            ]),
            ('8.5.5', 'Actividades posteriores a la entrega', '8.5', 5, [
                ('La organización debe cumplir los requisitos para las actividades posteriores a la entrega asociadas con los productos y servicios.', True, 'medium'),
            ]),
            ('8.5.6', 'Control de los cambios', '8.5', 6, [
                ('La organización debe revisar y controlar los cambios para la producción o la prestación del servicio, en la medida necesaria para asegurarse de la conformidad continua con los requisitos especificados.', True, 'high'),
            ]),
            ('8.6', 'Liberación de los productos y servicios', '8', 6, [
                ('La organización debe implementar las disposiciones planificadas, en las etapas adecuadas, para verificar que se cumplen los requisitos de los productos y servicios.', True, 'high'),
                ('La organización debe conservar la información documentada sobre la liberación de los productos y servicios.', True, 'high'),
            ]),
            ('8.7', 'Control de las salidas no conformes', '8', 7, [
                ('La organización debe asegurarse de que las salidas que no sean conformes con sus requisitos se identifican y se controlan para prevenir su uso o entrega no intencionados.', True, 'high'),
                ('La organización debe conservar información documentada que describa la no conformidad, las acciones tomadas y las concesiones obtenidas.', True, 'high'),
            ]),

            ('9', 'Evaluación del desempeño', None, 6, []),
            ('9.1', 'Seguimiento, medición, análisis y evaluación', '9', 1, []),
            ('9.1.1', 'Generalidades — seguimiento', '9.1', 1, [
                ('La organización debe determinar qué necesita seguimiento y medición, los métodos de seguimiento, medición, análisis y evaluación necesarios para asegurar resultados válidos.', True, 'high'),
                ('La organización debe conservar información documentada apropiada como evidencia de los resultados.', True, 'high'),
            ]),
            ('9.1.2', 'Satisfacción del cliente', '9.1', 2, [
                ('La organización debe realizar el seguimiento de las percepciones de los clientes del grado en que se cumplen sus necesidades y expectativas.', True, 'high'),
            ]),
            ('9.1.3', 'Análisis y evaluación', '9.1', 3, [
                ('La organización debe analizar y evaluar los datos y la información apropiados que surgen por el seguimiento y la medición.', True, 'high'),
            ]),
            ('9.2', 'Auditoría interna', '9', 2, []),
            ('9.2.1', 'Generalidades — auditoría interna', '9.2', 1, [
                ('La organización debe llevar a cabo auditorías internas a intervalos planificados para proporcionar información acerca de si el sistema de gestión de la calidad es conforme con los requisitos propios de la organización y los requisitos de esta Norma Internacional.', True, 'high'),
            ]),
            ('9.2.2', 'Programa de auditoría interna', '9.2', 2, [
                ('La organización debe planificar, establecer, implementar y mantener uno o varios programas de auditoría.', True, 'high'),
                ('La organización debe conservar información documentada como evidencia de la implementación del programa de auditoría y de los resultados de las auditorías.', True, 'high'),
            ]),
            ('9.3', 'Revisión por la dirección', '9', 3, []),
            ('9.3.1', 'Generalidades — revisión por la dirección', '9.3', 1, [
                ('La alta dirección debe revisar el sistema de gestión de la calidad de la organización a intervalos planificados, para asegurarse de su conveniencia, adecuación, eficacia y alineación continuas con la dirección estratégica de la organización.', True, 'high'),
            ]),
            ('9.3.2', 'Entradas de la revisión por la dirección', '9.3', 2, [
                ('La revisión por la dirección debe planificarse y llevarse a cabo incluyendo la consideración del estado de las acciones de las revisiones por la dirección previas y los cambios en las cuestiones externas e internas pertinentes al SGC.', True, 'high'),
            ]),
            ('9.3.3', 'Salidas de la revisión por la dirección', '9.3', 3, [
                ('Las salidas de la revisión por la dirección deben incluir las decisiones y acciones relacionadas con las oportunidades de mejora y cualquier necesidad de cambio en el sistema de gestión de la calidad.', True, 'high'),
                ('La organización debe conservar información documentada como evidencia de los resultados de las revisiones por la dirección.', True, 'high'),
            ]),

            ('10', 'Mejora', None, 7, []),
            ('10.1', 'Generalidades — mejora', '10', 1, [
                ('La organización debe determinar y seleccionar las oportunidades de mejora e implementar cualquier acción necesaria para cumplir los requisitos del cliente y aumentar la satisfacción del cliente.', True, 'high'),
            ]),
            ('10.2', 'No conformidad y acción correctiva', '10', 2, []),
            ('10.2.1', 'Acciones ante no conformidades', '10.2', 1, [
                ('Cuando ocurra una no conformidad, incluida cualquiera originada por quejas, la organización debe reaccionar ante la no conformidad tomando acciones para controlarla y corregirla.', True, 'high'),
                ('La organización debe evaluar la necesidad de acciones para eliminar las causas de la no conformidad, con el fin de que no vuelva a ocurrir ni ocurra en otra parte.', True, 'high'),
            ]),
            ('10.2.2', 'Información documentada de no conformidades', '10.2', 2, [
                ('La organización debe conservar información documentada como evidencia de la naturaleza de las no conformidades y cualquier acción tomada posteriormente, y de los resultados de cualquier acción correctiva.', True, 'high'),
            ]),
            ('10.3', 'Mejora continua', '10', 3, [
                ('La organización debe mejorar continuamente la conveniencia, adecuación y eficacia del sistema de gestión de la calidad.', True, 'high'),
            ]),
        ]

        self._create_clauses_and_requirements(iso, data)
        return iso

    # ─────────────────────────────────────────────
    # AS9100 Rev D
    # ─────────────────────────────────────────────

    def _create_as9100(self):
        as9100 = Standard.objects.create(
            name='AS9100 Rev D',
            version='Rev D',
            sector='Aeroespacial',
            is_active=True,
        )
        self.stdout.write('  Creando AS9100 Rev D...')

        data = [
            ('4', 'Contexto de la organización', None, 1, []),
            ('4.1', 'Comprensión de la organización y de su contexto', '4', 1, [
                ('La organización debe determinar las cuestiones externas e internas que son pertinentes para su propósito y su dirección estratégica, y que afectan a su capacidad para lograr los resultados previstos de su sistema de gestión de la calidad.', True, 'high'),
                ('La organización debe realizar el seguimiento y la revisión de la información sobre estas cuestiones externas e internas.', True, 'medium'),
            ]),
            ('4.2', 'Comprensión de las necesidades y expectativas de las partes interesadas', '4', 2, [
                ('La organización debe determinar las partes interesadas que son pertinentes al sistema de gestión de la calidad y los requisitos pertinentes de estas partes interesadas, incluidos los requisitos estatutarios y reglamentarios aplicables.', True, 'high'),
                ('La organización debe realizar el seguimiento y la revisión de la información sobre estas partes interesadas y sus requisitos pertinentes.', True, 'medium'),
            ]),
            ('4.3', 'Determinación del alcance del sistema de gestión de la calidad', '4', 3, [
                ('La organización debe determinar los límites y la aplicabilidad del sistema de gestión de la calidad para establecer su alcance, considerando los productos y servicios de la organización y sus obligaciones de cumplimiento.', True, 'high'),
                ('El alcance debe estar disponible y mantenerse como información documentada e incluir los tipos de productos y servicios cubiertos y la justificación de cualquier requisito de esta norma que la organización haya determinado que no es aplicable.', True, 'high'),
            ]),
            ('4.4', 'Sistema de gestión de la calidad y sus procesos', '4', 4, [
                ('La organización debe establecer, implementar, mantener y mejorar continuamente un sistema de gestión de la calidad, incluidos los procesos necesarios y sus interacciones, de acuerdo con los requisitos de esta norma internacional.', True, 'high'),
                ('La organización debe mantener información documentada para apoyar la operación de sus procesos y conservar información documentada para tener la confianza de que los procesos se realizan según lo planificado.', True, 'high'),
            ]),

            ('5', 'Liderazgo', None, 2, []),
            ('5.1', 'Liderazgo y compromiso', '5', 1, []),
            ('5.1.1', 'Generalidades — liderazgo', '5.1', 1, [
                ('La alta dirección debe demostrar liderazgo y compromiso con respecto al sistema de gestión de la calidad asumiendo la responsabilidad y obligación de rendir cuentas con relación a la eficacia del SGC.', True, 'high'),
                ('La alta dirección debe asegurarse de que se establezcan la política de la calidad y los objetivos de la calidad para el sistema de gestión de la calidad y que sean compatibles con el contexto y la dirección estratégica de la organización.', True, 'high'),
                ('La alta dirección debe asegurarse de que la organización establezca y comunique la importancia de cumplir los requisitos del cliente, así como los requisitos legales y reglamentarios aplicables.', True, 'high'),
            ]),
            ('5.1.2', 'Enfoque al cliente', '5.1', 2, [
                ('La alta dirección debe demostrar liderazgo y compromiso con respecto al enfoque al cliente asegurándose de que se determinan, se comprenden y se cumplen regularmente los requisitos del cliente y los requisitos legales y reglamentarios aplicables.', True, 'high'),
                ('La alta dirección debe asegurarse de que se mantiene el enfoque en aumentar la satisfacción del cliente.', True, 'medium'),
            ]),
            ('5.2', 'Política', '5', 2, []),
            ('5.2.1', 'Establecimiento de la política de la calidad', '5.2', 1, [
                ('La alta dirección debe establecer, implementar y mantener una política de la calidad que sea apropiada al propósito y contexto de la organización y apoye su dirección estratégica.', True, 'high'),
                ('La política de la calidad debe proporcionar un marco de referencia para el establecimiento de los objetivos de la calidad e incluir un compromiso de cumplir los requisitos aplicables.', True, 'high'),
            ]),
            ('5.2.2', 'Comunicación de la política de la calidad', '5.2', 2, [
                ('La política de la calidad debe estar disponible y mantenerse como información documentada, comunicarse, entenderse y aplicarse dentro de la organización y estar disponible para las partes interesadas pertinentes.', True, 'high'),
            ]),
            ('5.3', 'Roles, responsabilidades y autoridades en la organización', '5', 3, [
                ('La alta dirección debe asegurarse de que las responsabilidades y autoridades para los roles pertinentes se asignen, se comuniquen y se entiendan en toda la organización.', True, 'high'),
                ('La alta dirección debe asignar la responsabilidad y autoridad para asegurarse de que el SGC es conforme con los requisitos de esta norma y para informar sobre el desempeño del SGC a la alta dirección.', True, 'high'),
            ]),

            ('6', 'Planificación', None, 3, []),
            ('6.1', 'Acciones para abordar riesgos y oportunidades', '6', 1, []),
            ('6.1.1', 'Generalidades — riesgos y oportunidades', '6.1', 1, [
                ('Al planificar el sistema de gestión de la calidad, la organización debe considerar las cuestiones del contexto y los requisitos de las partes interesadas y determinar los riesgos y oportunidades que es necesario abordar.', True, 'high'),
                ('La organización debe considerar los riesgos relacionados con la aeronavegabilidad de los productos y servicios cuando determine los riesgos y oportunidades.', True, 'high', True),
            ]),
            ('6.1.2', 'Acciones sobre riesgos y oportunidades', '6.1', 2, [
                ('La organización debe planificar las acciones para abordar estos riesgos y oportunidades, cómo integrar e implementar las acciones en sus procesos del SGC y evaluar la eficacia de estas acciones.', True, 'high'),
            ]),
            ('6.2', 'Objetivos de la calidad y planificación para lograrlos', '6', 2, [
                ('La organización debe establecer objetivos de la calidad para las funciones y niveles pertinentes y los procesos necesarios para el sistema de gestión de la calidad.', True, 'high'),
                ('Los objetivos de la calidad deben ser medibles, tener en cuenta los requisitos aplicables y ser pertinentes para la conformidad de los productos y servicios y para el aumento de la satisfacción del cliente.', True, 'high'),
                ('La organización debe mantener información documentada sobre los objetivos de la calidad.', True, 'medium'),
            ]),
            ('6.3', 'Planificación de los cambios', '6', 3, [
                ('Cuando la organización determine la necesidad de cambios en el sistema de gestión de la calidad, estos cambios se deben llevar a cabo de manera planificada, considerando el propósito de los cambios y sus posibles consecuencias.', True, 'medium'),
            ]),

            ('7', 'Apoyo', None, 4, []),
            ('7.1', 'Recursos', '7', 1, []),
            ('7.1.1', 'Generalidades — recursos', '7.1', 1, [
                ('La organización debe determinar y proporcionar los recursos necesarios para el establecimiento, implementación, mantenimiento y mejora continua del sistema de gestión de la calidad.', True, 'high'),
            ]),
            ('7.1.2', 'Personas', '7.1', 2, [
                ('La organización debe determinar y proporcionar las personas necesarias para la implementación eficaz de su sistema de gestión de la calidad y para la operación y control de sus procesos.', True, 'high'),
            ]),
            ('7.1.3', 'Infraestructura', '7.1', 3, [
                ('La organización debe determinar, proporcionar y mantener la infraestructura necesaria para la operación de sus procesos y lograr la conformidad de los productos y servicios.', True, 'medium'),
            ]),
            ('7.1.4', 'Ambiente para la operación de los procesos', '7.1', 4, [
                ('La organización debe determinar, proporcionar y mantener el ambiente necesario para la operación de sus procesos y para lograr la conformidad de los productos y servicios, considerando los factores humanos y físicos.', True, 'medium'),
            ]),
            ('7.1.5', 'Recursos de seguimiento y medición', '7.1', 5, [
                ('La organización debe determinar y proporcionar los recursos necesarios para asegurarse de la validez y fiabilidad de los resultados cuando se realice seguimiento o medición para verificar la conformidad de los productos y servicios con los requisitos.', True, 'high'),
                ('La organización debe asegurarse de que los recursos proporcionados son apropiados para el tipo específico de actividades de seguimiento y medición realizadas y se mantienen para asegurarse de la idoneidad continua para su propósito.', True, 'high'),
            ]),
            ('7.1.6', 'Conocimientos de la organización', '7.1', 6, [
                ('La organización debe determinar los conocimientos necesarios para la operación de sus procesos y para lograr la conformidad de los productos y servicios. Estos conocimientos deben mantenerse y ponerse a disposición en la medida en que sea necesario.', True, 'medium'),
            ]),
            ('7.2', 'Competencia', '7', 2, [
                ('La organización debe determinar la competencia necesaria de las personas que realizan, bajo su control, un trabajo que afecta al desempeño y eficacia del SGC.', True, 'high'),
                ('La organización debe asegurarse de que estas personas sean competentes, basándose en la educación, formación o experiencia apropiadas, y tomar acciones para adquirir la competencia necesaria y evaluar la eficacia de las acciones tomadas.', True, 'high'),
                ('La organización debe conservar información documentada apropiada como evidencia de la competencia.', True, 'high'),
            ]),
            ('7.3', 'Toma de conciencia', '7', 3, [
                ('La organización debe asegurarse de que las personas que realizan el trabajo bajo el control de la organización tomen conciencia de la política de la calidad, los objetivos de la calidad pertinentes y su contribución a la eficacia del SGC.', True, 'medium'),
            ]),
            ('7.4', 'Comunicación', '7', 4, [
                ('La organización debe determinar las comunicaciones internas y externas pertinentes al sistema de gestión de la calidad, incluyendo sobre qué comunicar, cuándo comunicar, a quién comunicar y cómo comunicar.', True, 'medium'),
            ]),
            ('7.5', 'Información documentada', '7', 5, []),
            ('7.5.1', 'Generalidades — información documentada', '7.5', 1, [
                ('El sistema de gestión de la calidad de la organización debe incluir la información documentada requerida por esta norma y la determinada por la organización como necesaria para la eficacia del SGC.', True, 'high'),
            ]),
            ('7.5.2', 'Creación y actualización', '7.5', 2, [
                ('Al crear y actualizar la información documentada, la organización debe asegurarse de que sea apropiada la identificación y descripción, el formato y los medios de soporte, y la revisión y aprobación con respecto a la conveniencia y adecuación.', True, 'high'),
            ]),
            ('7.5.3', 'Control de la información documentada', '7.5', 3, [
                ('La información documentada requerida por el SGC y por esta norma se debe controlar para asegurarse de que esté disponible y sea idónea para su uso, donde y cuando se necesite, y esté protegida adecuadamente.', True, 'high'),
                ('La organización debe abordar la distribución, acceso, recuperación y uso, almacenamiento y preservación, control de cambios y conservación y disposición de la información documentada.', True, 'high'),
            ]),

            ('8', 'Operación', None, 5, []),
            ('8.1', 'Planificación y control operacional', '8', 1, [
                ('La organización debe planificar, implementar, controlar, hacer seguimiento y revisar los procesos necesarios para cumplir los requisitos para la provisión de productos y servicios.', True, 'high'),
                ('La organización debe conservar información documentada en la medida necesaria para tener confianza en que los procesos se han llevado a cabo según lo planificado.', True, 'high'),
            ]),
            ('8.1.1', 'Planificación operacional — requisitos aeroespaciales', '8.1', 2, [
                ('La organización debe determinar los riesgos y oportunidades relacionados con el logro de los requisitos planificados para los productos y servicios, con el fin de implementar acciones apropiadas.', True, 'high', True),
                ('La organización debe aplicar la gestión de la configuración según sea apropiado para cumplir los requisitos del cliente y del producto.', True, 'high', True),
                ('La organización debe establecer un proceso para la determinación y gestión del trabajo transferido temporalmente fuera de las instalaciones.', True, 'medium', True),
            ]),
            ('8.1.2', 'Gestión de la configuración', '8.1', 3, [
                ('La organización debe establecer, implementar y mantener un proceso de gestión de la configuración que incluya la identificación de la configuración, el control de la configuración, el registro del estado de la configuración y la auditoría de la configuración.', True, 'high', True),
                ('La organización debe asegurarse de que la documentación de la configuración refleja el estado actual del producto o servicio.', True, 'high', True),
            ]),
            ('8.1.3', 'Control de productos y servicios suministrados externamente — aeroespacial', '8.1', 4, [
                ('La organización debe comunicar sus requisitos a los proveedores externos, incluyendo los requisitos del cliente aplicables y los requisitos estatutarios y reglamentarios pertinentes.', True, 'high', True),
                ('La organización debe asegurarse de que las personas que interactúan con los proveedores externos son competentes.', True, 'medium', True),
            ]),
            ('8.2', 'Requisitos para los productos y servicios', '8', 2, []),
            ('8.2.1', 'Comunicación con el cliente', '8.2', 1, [
                ('La comunicación con los clientes debe incluir proporcionar la información relativa a los productos y servicios, tratar las consultas y los contratos o pedidos, incluyendo los cambios, y obtener la retroalimentación de los clientes relativa a los productos y servicios.', True, 'medium'),
            ]),
            ('8.2.2', 'Determinación de los requisitos para productos y servicios', '8.2', 2, [
                ('La organización debe asegurarse de que tiene la capacidad de cumplir los requisitos para los productos y servicios que se van a ofrecer a los clientes, incluyendo los requisitos legales y reglamentarios aplicables.', True, 'high'),
            ]),
            ('8.2.3', 'Revisión de los requisitos para productos y servicios', '8.2', 3, [
                ('La organización debe asegurarse de que tiene la capacidad de cumplir los requisitos para los productos y servicios antes de comprometerse a suministrarlos al cliente.', True, 'high'),
                ('La organización debe conservar información documentada sobre los resultados de la revisión y sobre cualquier requisito nuevo para los productos y servicios.', True, 'high'),
            ]),
            ('8.2.4', 'Cambios en los requisitos para productos y servicios', '8.2', 4, [
                ('La organización debe asegurarse de que la información documentada pertinente sea modificada y de que las personas pertinentes sean conscientes de los requisitos modificados cuando se cambien los requisitos para los productos y servicios.', True, 'medium'),
            ]),
            ('8.3', 'Diseño y desarrollo de los productos y servicios', '8', 3, []),
            ('8.3.1', 'Generalidades — diseño y desarrollo', '8.3', 1, [
                ('La organización debe establecer, implementar y mantener un proceso de diseño y desarrollo que sea adecuado para asegurarse de la posterior provisión de productos y servicios.', True, 'high'),
            ]),
            ('8.3.2', 'Planificación del diseño y desarrollo', '8.3', 2, [
                ('Al determinar las etapas y controles para el diseño y desarrollo, la organización debe considerar la naturaleza, duración y complejidad de las actividades de diseño y desarrollo y los requisitos de revisión, verificación y validación aplicables.', True, 'high'),
                ('La organización debe establecer criterios de diseño y desarrollo, incluyendo criterios de rendimiento y seguridad del producto, y mantener información documentada sobre los mismos.', True, 'high', True),
            ]),
            ('8.3.3', 'Entradas para el diseño y desarrollo', '8.3', 3, [
                ('La organización debe determinar los requisitos esenciales para los tipos específicos de productos y servicios a diseñar y desarrollar, incluyendo los requisitos funcionales y de desempeño y los requisitos legales y reglamentarios aplicables.', True, 'high'),
                ('La organización debe considerar los resultados de actividades previas de diseño y desarrollo similares y las consecuencias de un posible fallo.', True, 'high', True),
            ]),
            ('8.3.4', 'Controles del diseño y desarrollo', '8.3', 4, [
                ('La organización debe aplicar controles al proceso de diseño y desarrollo para asegurarse de que se definen los resultados a lograr, se realizan las revisiones para evaluar la capacidad de los resultados de cumplir los requisitos.', True, 'high'),
                ('La organización debe asegurarse de que se realizan actividades de verificación del diseño para confirmar que las salidas del diseño y desarrollo cumplen los requisitos de las entradas.', True, 'high'),
            ]),
            ('8.3.5', 'Salidas del diseño y desarrollo', '8.3', 5, [
                ('La organización debe asegurarse de que las salidas del diseño y desarrollo cumplen los requisitos de las entradas, son adecuadas para los procesos posteriores de provisión de productos y servicios e incluyen o hacen referencia a los requisitos de seguimiento y medición.', True, 'high'),
            ]),
            ('8.3.6', 'Cambios del diseño y desarrollo', '8.3', 6, [
                ('La organización debe identificar, revisar y controlar los cambios hechos durante el diseño y desarrollo de los productos y servicios, o posteriormente, en la medida necesaria para asegurarse de que no haya un impacto adverso en la conformidad con los requisitos.', True, 'high'),
                ('La organización debe asegurarse de que los cambios de diseño y desarrollo están autorizados antes de su implementación y de que las partes afectadas son notificadas.', True, 'high', True),
            ]),
            ('8.4', 'Control de los procesos, productos y servicios suministrados externamente', '8', 4, []),
            ('8.4.1', 'Generalidades — control externo', '8.4', 1, [
                ('La organización debe asegurarse de que los procesos, productos y servicios suministrados externamente son conformes a los requisitos especificados.', True, 'high'),
                ('La organización debe mantener una lista de proveedores aprobados y debe asegurarse de que los proveedores aprobados están calificados antes de ser utilizados.', True, 'high', True),
            ]),
            ('8.4.2', 'Tipo y alcance del control', '8.4', 2, [
                ('La organización debe asegurarse de que los procesos, productos y servicios suministrados externamente no afectan de manera adversa a la capacidad de la organización de entregar productos y servicios conformes de manera coherente a sus clientes.', True, 'high'),
                ('La organización debe llevar a cabo actividades de seguimiento del desempeño de los proveedores externos y debe tomar las acciones apropiadas cuando los proveedores no cumplan los requisitos.', True, 'high', True),
            ]),
            ('8.4.3', 'Información para los proveedores externos', '8.4', 3, [
                ('La organización debe comunicar a los proveedores externos sus requisitos para los procesos, productos y servicios a proporcionar, incluyendo los requisitos del cliente aplicables y los requisitos de flujo descendente aplicables.', True, 'medium'),
            ]),
            ('8.5', 'Producción y provisión del servicio', '8', 5, []),
            ('8.5.1', 'Control de la producción y de la provisión del servicio', '8.5', 1, [
                ('La organización debe implementar la producción y provisión del servicio bajo condiciones controladas.', True, 'high'),
                ('Las condiciones controladas deben incluir la disponibilidad de información documentada que defina las características de los productos a producir y la disponibilidad y uso de recursos de seguimiento y medición adecuados.', True, 'high'),
                ('La organización debe implementar actividades de liberación, entrega y posteriores a la entrega del producto.', True, 'high'),
                ('La organización debe asegurarse de que el personal que realiza trabajos que afectan a la conformidad del producto está cualificado según los criterios definidos.', True, 'high', True),
                ('La organización debe establecer y mantener un proceso para la gestión y el control de los documentos de trabajo, incluyendo instrucciones de trabajo y planos.', True, 'high', True),
            ]),
            ('8.5.2', 'Identificación y trazabilidad', '8.5', 2, [
                ('La organización debe utilizar los medios apropiados para identificar las salidas cuando sea necesario para asegurar la conformidad de los productos y servicios.', True, 'high'),
                ('La organización debe controlar la identificación única de las salidas cuando la trazabilidad sea un requisito y debe conservar la información documentada necesaria para permitir la trazabilidad.', True, 'high'),
                ('La organización debe controlar todos los medios de producción y provisión del servicio, incluidos el hardware, el software, las herramientas y los entornos de trabajo.', True, 'high', True),
            ]),
            ('8.5.3', 'Propiedad perteneciente a los clientes o proveedores externos', '8.5', 3, [
                ('La organización debe cuidar la propiedad perteneciente a los clientes o a proveedores externos mientras esté bajo el control de la organización o esté siendo utilizada por la misma, e identificar, verificar, proteger y salvaguardar la propiedad del cliente o del proveedor externo.', True, 'medium'),
            ]),
            ('8.5.4', 'Preservación', '8.5', 4, [
                ('La organización debe preservar las salidas durante la producción y prestación del servicio, en la medida necesaria para asegurarse de la conformidad con los requisitos, incluyendo la identificación, manipulación, contaminación, embalaje, almacenamiento, transmisión o transporte y protección.', True, 'medium'),
            ]),
            ('8.5.5', 'Actividades posteriores a la entrega', '8.5', 5, [
                ('La organización debe cumplir los requisitos para las actividades posteriores a la entrega asociadas con los productos y servicios, considerando los requisitos legales y reglamentarios, las consecuencias no deseadas potenciales asociadas a sus productos y servicios y los requisitos del cliente.', True, 'medium'),
            ]),
            ('8.5.6', 'Control de los cambios', '8.5', 6, [
                ('La organización debe revisar y controlar los cambios para la producción o la prestación del servicio, en la medida necesaria para asegurarse de la conformidad continua con los requisitos especificados.', True, 'high'),
                ('La organización debe asegurarse de que los cambios en los procesos de producción están documentados y aprobados antes de su implementación.', True, 'high', True),
            ]),
            ('8.6', 'Liberación de los productos y servicios', '8', 6, [
                ('La organización debe implementar las disposiciones planificadas, en las etapas adecuadas, para verificar que se cumplen los requisitos de los productos y servicios.', True, 'high'),
                ('La organización debe conservar la información documentada sobre la liberación de los productos y servicios e incluir evidencia de la conformidad con los criterios de aceptación e indicar la(s) persona(s) que autorizan la liberación.', True, 'high'),
                ('La organización debe asegurarse de que los documentos y registros requeridos están completos y presentes en los puntos de verificación final del producto antes de la entrega al cliente.', True, 'high', True),
            ]),
            ('8.7', 'Control de las salidas no conformes', '8', 7, [
                ('La organización debe asegurarse de que las salidas que no sean conformes con sus requisitos se identifican y se controlan para prevenir su uso o entrega no intencionados.', True, 'high'),
                ('La organización debe conservar información documentada que describa la no conformidad, las acciones tomadas, las concesiones obtenidas e identifique la autoridad que decide la acción con respecto a la no conformidad.', True, 'high'),
                ('La organización debe notificar al cliente y a las autoridades reglamentarias pertinentes cuando se detecten productos no conformes después de la entrega.', True, 'high', True),
            ]),

            ('9', 'Evaluación del desempeño', None, 6, []),
            ('9.1', 'Seguimiento, medición, análisis y evaluación', '9', 1, []),
            ('9.1.1', 'Generalidades — seguimiento', '9.1', 1, [
                ('La organización debe determinar qué necesita seguimiento y medición, los métodos de seguimiento, medición, análisis y evaluación necesarios para asegurar resultados válidos y cuándo se deben llevar a cabo el seguimiento y la medición.', True, 'high'),
                ('La organización debe conservar información documentada apropiada como evidencia de los resultados del seguimiento y medición.', True, 'high'),
            ]),
            ('9.1.2', 'Satisfacción del cliente', '9.1', 2, [
                ('La organización debe realizar el seguimiento de las percepciones de los clientes del grado en que se cumplen sus necesidades y expectativas.', True, 'high'),
                ('La organización debe obtener información sobre la satisfacción del cliente a través de métodos definidos.', True, 'medium'),
            ]),
            ('9.1.3', 'Análisis y evaluación', '9.1', 3, [
                ('La organización debe analizar y evaluar los datos y la información apropiados que surgen por el seguimiento y la medición para evaluar la conformidad de los productos y servicios, el grado de satisfacción del cliente y el desempeño y la eficacia del SGC.', True, 'high'),
            ]),
            ('9.2', 'Auditoría interna', '9', 2, []),
            ('9.2.1', 'Generalidades — auditoría interna', '9.2', 1, [
                ('La organización debe llevar a cabo auditorías internas a intervalos planificados para proporcionar información acerca de si el sistema de gestión de la calidad es conforme con los requisitos propios de la organización, los requisitos de esta norma y los requisitos del cliente aplicables.', True, 'high'),
            ]),
            ('9.2.2', 'Programa de auditoría interna', '9.2', 2, [
                ('La organización debe planificar, establecer, implementar y mantener uno o varios programas de auditoría que incluyan la frecuencia, los métodos, las responsabilidades, los requisitos de planificación y la elaboración de informes.', True, 'high'),
                ('La organización debe conservar información documentada como evidencia de la implementación del programa de auditoría y de los resultados de las auditorías.', True, 'high'),
            ]),
            ('9.3', 'Revisión por la dirección', '9', 3, []),
            ('9.3.1', 'Generalidades — revisión por la dirección', '9.3', 1, [
                ('La alta dirección debe revisar el sistema de gestión de la calidad de la organización a intervalos planificados, para asegurarse de su conveniencia, adecuación, eficacia y alineación continuas con la dirección estratégica de la organización.', True, 'high'),
            ]),
            ('9.3.2', 'Entradas de la revisión por la dirección', '9.3', 2, [
                ('La revisión por la dirección debe planificarse y llevarse a cabo incluyendo la consideración del estado de las acciones de las revisiones previas, los cambios en las cuestiones externas e internas pertinentes al SGC y el desempeño y la eficacia del SGC.', True, 'high'),
            ]),
            ('9.3.3', 'Salidas de la revisión por la dirección', '9.3', 3, [
                ('Las salidas de la revisión por la dirección deben incluir las decisiones y acciones relacionadas con las oportunidades de mejora, cualquier necesidad de cambio en el SGC y las necesidades de recursos.', True, 'high'),
                ('La organización debe conservar información documentada como evidencia de los resultados de las revisiones por la dirección.', True, 'high'),
            ]),

            ('10', 'Mejora', None, 7, []),
            ('10.1', 'Generalidades — mejora', '10', 1, [
                ('La organización debe determinar y seleccionar las oportunidades de mejora e implementar cualquier acción necesaria para cumplir los requisitos del cliente y aumentar la satisfacción del cliente.', True, 'high'),
            ]),
            ('10.2', 'No conformidad y acción correctiva', '10', 2, []),
            ('10.2.1', 'Acciones ante no conformidades', '10.2', 1, [
                ('Cuando ocurra una no conformidad, incluida cualquiera originada por quejas, la organización debe reaccionar ante la no conformidad tomando acciones para controlarla, corregirla y hacer frente a las consecuencias.', True, 'high'),
                ('La organización debe evaluar la necesidad de acciones para eliminar las causas de la no conformidad mediante la revisión y el análisis de la no conformidad, la determinación de las causas de la no conformidad y la determinación de si existen no conformidades similares.', True, 'high'),
                ('La organización debe notificar a las organizaciones externas pertinentes sobre las no conformidades que afecten a sus productos o servicios.', True, 'high', True),
            ]),
            ('10.2.2', 'Información documentada de no conformidades', '10.2', 2, [
                ('La organización debe conservar información documentada como evidencia de la naturaleza de las no conformidades y cualquier acción tomada posteriormente, y de los resultados de cualquier acción correctiva.', True, 'high'),
            ]),
            ('10.3', 'Mejora continua', '10', 3, [
                ('La organización debe mejorar continuamente la conveniencia, adecuación y eficacia del sistema de gestión de la calidad, considerando los resultados del análisis y la evaluación, y las salidas de la revisión por la dirección para determinar si hay necesidades u oportunidades que deben considerarse como parte de la mejora continua.', True, 'high'),
            ]),
        ]

        self._create_clauses_and_requirements(as9100, data)
        return as9100

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────

    def _create_clauses_and_requirements(self, standard, data):
        clause_map = {}

        for entry in data:
            if len(entry) == 5:
                code, title, parent_code, ordering, requirements = entry
            else:
                continue

            parent = clause_map.get(parent_code) if parent_code else None

            clause = Clause.objects.create(
                standard=standard,
                code=code,
                title=title,
                parent=parent,
                ordering=ordering,
            )
            clause_map[code] = clause

            for i, req in enumerate(requirements):
                if len(req) == 3:
                    text, mandatory, criticality = req
                    is_extension = False
                elif len(req) == 4:
                    text, mandatory, criticality, is_extension = req
                else:
                    continue

                StandardRequirement.objects.create(
                    clause=clause,
                    text=text,
                    mandatory=mandatory,
                    criticality_level=criticality,
                    is_extension=is_extension,
                    ordering=i + 1,
                )

    def _create_mappings(self, iso, as9100):
        self.stdout.write('  Creando mapeos ISO 9001 ↔ AS9100...')

        mapping_data = [
            ('4.1', '4.1', 'EQUIVALENT'),
            ('4.2', '4.2', 'SUPERSET'),
            ('4.3', '4.3', 'SUPERSET'),
            ('4.4', '4.4', 'EQUIVALENT'),
            ('5.1.1', '5.1.1', 'SUPERSET'),
            ('5.1.2', '5.1.2', 'EQUIVALENT'),
            ('5.2.1', '5.2.1', 'SUPERSET'),
            ('5.2.2', '5.2.2', 'SUPERSET'),
            ('5.3', '5.3', 'SUPERSET'),
            ('6.1.1', '6.1.1', 'SUPERSET'),
            ('6.1.2', '6.1.2', 'EQUIVALENT'),
            ('6.2', '6.2', 'SUPERSET'),
            ('6.3', '6.3', 'SUPERSET'),
            ('7.1.1', '7.1.1', 'EQUIVALENT'),
            ('7.1.2', '7.1.2', 'EQUIVALENT'),
            ('7.1.3', '7.1.3', 'EQUIVALENT'),
            ('7.1.4', '7.1.4', 'SUPERSET'),
            ('7.1.5', '7.1.5', 'SUPERSET'),
            ('7.1.6', '7.1.6', 'SUPERSET'),
            ('7.2', '7.2', 'SUPERSET'),
            ('7.3', '7.3', 'SUPERSET'),
            ('7.4', '7.4', 'SUPERSET'),
            ('7.5.1', '7.5.1', 'EQUIVALENT'),
            ('7.5.2', '7.5.2', 'EQUIVALENT'),
            ('7.5.3', '7.5.3', 'SUPERSET'),
            ('8.1', '8.1', 'SUPERSET'),
            ('8.2.1', '8.2.1', 'SUPERSET'),
            ('8.2.2', '8.2.2', 'SUPERSET'),
            ('8.2.3', '8.2.3', 'SUPERSET'),
            ('8.2.4', '8.2.4', 'EQUIVALENT'),
            ('8.3.1', '8.3.1', 'EQUIVALENT'),
            ('8.3.2', '8.3.2', 'SUPERSET'),
            ('8.3.3', '8.3.3', 'SUPERSET'),
            ('8.3.4', '8.3.4', 'SUPERSET'),
            ('8.3.5', '8.3.5', 'SUPERSET'),
            ('8.3.6', '8.3.6', 'SUPERSET'),
            ('8.4.1', '8.4.1', 'SUPERSET'),
            ('8.4.2', '8.4.2', 'SUPERSET'),
            ('8.4.3', '8.4.3', 'SUPERSET'),
            ('8.5.1', '8.5.1', 'SUPERSET'),
            ('8.5.2', '8.5.2', 'SUPERSET'),
            ('8.5.3', '8.5.3', 'SUPERSET'),
            ('8.5.4', '8.5.4', 'SUPERSET'),
            ('8.5.5', '8.5.5', 'SUPERSET'),
            ('8.5.6', '8.5.6', 'SUPERSET'),
            ('8.6', '8.6', 'SUPERSET'),
            ('8.7', '8.7', 'SUPERSET'),
            ('9.1.1', '9.1.1', 'SUPERSET'),
            ('9.1.2', '9.1.2', 'SUPERSET'),
            ('9.1.3', '9.1.3', 'SUPERSET'),
            ('9.2.1', '9.2.1', 'SUPERSET'),
            ('9.2.2', '9.2.2', 'SUPERSET'),
            ('9.3.1', '9.3.1', 'EQUIVALENT'),
            ('9.3.2', '9.3.2', 'SUPERSET'),
            ('9.3.3', '9.3.3', 'SUPERSET'),
            ('10.1', '10.1', 'EQUIVALENT'),
            ('10.2.1', '10.2.1', 'SUPERSET'),
            ('10.2.2', '10.2.2', 'EQUIVALENT'),
            ('10.3', '10.3', 'SUPERSET'),
        ]

        for iso_code, as_code, mapping_type in mapping_data:
            try:
                iso_clause = Clause.objects.get(standard=iso, code=iso_code)
                as_clause = Clause.objects.get(standard=as9100, code=as_code)

                iso_req = StandardRequirement.objects.filter(
                    clause=iso_clause
                ).first()
                as_req = StandardRequirement.objects.filter(
                    clause=as_clause
                ).first()

                if iso_req and as_req:
                    StandardMapping.objects.create(
                        source_requirement=iso_req,
                        target_requirement=as_req,
                        mapping_type=mapping_type,
                    )
            except Clause.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'  Cláusula no encontrada: ISO {iso_code} o AS9100 {as_code}'
                ))