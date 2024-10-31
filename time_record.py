from datetime import datetime
from database import DatabaseConnection
from payment_period import PaymentPeriod
import pandas as pd


class TimeRecord:
    def __init__(self, project_id, person_id, date, hours=0, horas_ext=0, horas_ext_noct=0, horas_fest=0,
                 horas_ext_fest_noct=0, horas_noct=0, horas_noct_fest=0):
        self.project_id = project_id
        self.person_id = person_id
        self.date = date
        self.hours = hours
        self.horas_ext = horas_ext
        self.horas_ext_noct = horas_ext_noct
        self.horas_fest = horas_fest
        self.horas_ext_fest_noct = horas_ext_fest_noct
        self.horas_noct = horas_noct
        self.horas_noct_fest = horas_noct_fest

    def save(self, db_connection):
        query = """
            INSERT INTO salario (fecha, project_id, person_id, horas)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE horas = VALUES(horas)
        """
        params = (self.date, self.project_id, self.person_id, self.hours)
        db_connection.execute_query(query, params)
        db_connection.commit()

class TimeRecorder:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def is_holiday(self, date):
        # Lista de festivos. Agrega las fechas que consideres necesarias.
        holidays = [
            datetime(2024, 1, 1),  # Ejemplo: Año Nuevo
            datetime(2024, 5, 1),  # Ejemplo: Día del Trabajo
            datetime(2024, 11, 4),
            datetime(2024, 11, 11),
            # Agrega más días festivos según corresponda
        ]
        # Retorna True si la fecha es un festivo
        return date in holidays

    def get_tasks_data(self, start_date, end_date):
        query = """
            SELECT 
                DATE(d.date) AS task_date, 
                pt.project_id, 
                u.person_id, 
                CASE 
                    WHEN COALESCE(SUM(TIMESTAMPDIFF(HOUR, 
                        GREATEST(pt.start_date, d.date), 
                        LEAST(pt.end_date, DATE_ADD(d.date, INTERVAL 1 DAY))
                    )), 0) > 9 THEN 9 
                    ELSE COALESCE(SUM(TIMESTAMPDIFF(HOUR, 
                        GREATEST(pt.start_date, d.date), 
                        LEAST(pt.end_date, DATE_ADD(d.date, INTERVAL 1 DAY))
                    )), 0) 
                END AS total_hours
            FROM (
                SELECT DATE_ADD(%s, INTERVAL n.n DAY) AS date
                FROM (
                    SELECT 0 AS n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 
                    UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 
                    UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11 
                    UNION ALL SELECT 12 UNION ALL SELECT 13 UNION ALL SELECT 14 UNION ALL SELECT 15 
                    UNION ALL SELECT 16 UNION ALL SELECT 17 UNION ALL SELECT 18 UNION ALL SELECT 19 
                    UNION ALL SELECT 20 UNION ALL SELECT 21 UNION ALL SELECT 22 UNION ALL SELECT 23 
                    UNION ALL SELECT 24 UNION ALL SELECT 25 UNION ALL SELECT 26 UNION ALL SELECT 27 
                    UNION ALL SELECT 28 UNION ALL SELECT 29 UNION ALL SELECT 30
                ) AS n
                WHERE DATE_ADD(%s, INTERVAL n.n DAY) <= %s
            ) d
            JOIN `project-tasks` pt ON pt.start_date <= DATE_ADD(d.date, INTERVAL 1 DAY) 
                AND (pt.end_date >= d.date OR pt.end_date IS NULL)
                AND pt.is_deleted = 0  -- Filtrar por tareas no eliminadas
            JOIN `project-tasks_installers_installers` ptii ON pt.id = ptii.projectTasksId
            JOIN `installers` i ON ptii.installersId = i.id
            JOIN `users` u ON i.user_id = u.id
            GROUP BY d.date, pt.project_id, u.person_id
            ORDER BY d.date, pt.project_id;
        """
        params = (start_date.date(), start_date.date(), end_date.date())
        cursor = self.db_connection.execute_query(query, params)
        return cursor.fetchall()

    def update_records(self, start_date, end_date):
        tasks_data = self.get_tasks_data(start_date, end_date)
        specified_person_ids = {56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 73, 74, 75}
        date_person_hours = {}

        # Recolectar y agrupar horas por fecha y persona
        for task_date, project_id, person_id, total_hours in tasks_data:
            if task_date.weekday() < 6 and not self.is_holiday(task_date):  # Solo procesar de lunes a sábado
                key = (task_date, person_id)
                if key not in date_person_hours:
                    date_person_hours[key] = []
                date_person_hours[key].append((project_id, total_hours))

        # Ajustar horas para cada día y persona
        for (task_date, person_id), records in date_person_hours.items():
            max_hours = 9 if task_date.weekday() < 5 else 1  # 9 horas para lunes-viernes, 1 hora para sábado
            total_day_hours = sum(record[1] for record in records)
            
            if total_day_hours > max_hours:
                # Reducir horas al registro con más horas
                records.sort(key=lambda x: -x[1])  # Ordenar de mayor a menor
                excess_hours = total_day_hours - max_hours
                for i, (project_id, hours) in enumerate(records):
                    if hours > excess_hours:
                        records[i] = (project_id, hours - excess_hours)
                        break
                    else:
                        excess_hours -= hours
                        records[i] = (project_id, 0)
            
            elif total_day_hours < max_hours:
                # Completar horas con un registro en el proyecto 311
                records.append((311, max_hours - total_day_hours))
            
            if len(records) >= 3:
                # Repartir horas equitativamente si hay 3 o más registros
                avg_hours = max_hours // len(records)
                remainder = max_hours % len(records)
                for i in range(len(records)):
                    records[i] = (records[i][0], avg_hours + (1 if i < remainder else 0))
            
            # Guardar registros ajustados
            for project_id, hours in records:
                if hours > 0:
                    record = TimeRecord(
                        project_id=project_id,
                        person_id=person_id,
                        date=task_date,
                        hours=hours
                    )
                    record.save(self.db_connection)
        
        # Crear registros para person_ids faltantes
        all_dates = set(task_date for task_date, _ in date_person_hours)
        for date in all_dates:
            max_hours = 9 if date.weekday() < 5 else 1  # 9 horas para lunes-viernes, 1 hora para sábado
            for person_id in specified_person_ids:
                if (date, person_id) not in date_person_hours:
                    record = TimeRecord(
                        project_id=311,
                        person_id=person_id,
                        date=date,
                        hours=max_hours
                    )
                    record.save(self.db_connection)
                    print(f"Created record for person_id {person_id} on {date} with {max_hours} hours")
        
        print('Update completed')

    def update_report(self):
        query = """
            SELECT 
                s.fecha,
                s.project_id,
                p.name AS project_name,  -- Campo con el nombre del proyecto
                s.person_id,
                pe.name AS person_name,  -- Campo con el nombre de la persona
                s.horas,
                s.horas_ext,
                s.horas_ext_noct,
                s.horas_fest,
                s.horas_ext_fest_noct,
                s.horas_noct,
                s.horas_noct_fest
            FROM 
                salario s
            JOIN 
                projects p ON s.project_id = p.id  -- Asume que 'id' es la clave primaria en 'projects'
            JOIN 
                persons pe ON s.person_id = pe.id  -- Asume que 'id' es la clave primaria en 'persons'
            ORDER BY 
                s.fecha, p.name, pe.name;
        """
        # Ejecutar la consulta y obtener los resultados
        cursor = self.db_connection.execute_query(query)
        data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]  # Obtener nombres de las columnas
        
        # Crear un DataFrame a partir de los resultados de la consulta
        df = pd.DataFrame(data, columns=columns)
        
        # Guardar el DataFrame en un archivo de Excel
        filename = 'reporte_salario.xlsx'
        df.to_excel(filename, index=False)
        print(f"Reporte guardado como {filename}")


    def register_special_data(self):
        today = datetime.today()
        period = PaymentPeriod(today)
        start_date, end_date = period.get_current_period()

        tasks_data = self.get_tasks_data(start_date, end_date)

        for project_id, person_id, _ in tasks_data:
            special_data = self.get_special_data(project_id, person_id, today)
            record = TimeRecord(
                project_id=project_id,
                person_id=person_id,
                date=today,
                hours=0,
                horas_ext=special_data.get('horas_ext', 0),
                horas_ext_noct=special_data.get('horas_ext_noct', 0),
                horas_fest=special_data.get('horas_fest', 0),
                horas_ext_fest_noct=special_data.get('horas_ext_fest_noct', 0),
                horas_noct=special_data.get('horas_noct', 0),
                horas_noct_fest=special_data.get('horas_noct_fest', 0)
            )
            record.save(self.db_connection)

    def get_special_data(self, project_id, person_id, date):
        print(f"Solicita datos adicionales para el proyecto {project_id} y persona {person_id} en la fecha {date}.")
        return {
            'horas_ext': int(input("Ingrese horas extras: ")),
            'horas_ext_noct': int(input("Ingrese horas extras nocturnas: ")),
            'horas_fest': int(input("Ingrese horas en festivo: ")),
            'horas_ext_fest_noct': int(input("Ingrese horas extras en festivo nocturno: ")),
            'horas_noct': int(input("Ingrese horas nocturnas: ")),
            'horas_noct_fest': int(input("Ingrese horas en festivo nocturno: "))
        }

