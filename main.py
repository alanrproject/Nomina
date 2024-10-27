from datetime import datetime
from database import DatabaseConnection
from payment_period import PaymentPeriod
from time_record import TimeRecorder

def main():
    # Conexión a la base de datos
    db_conn = DatabaseConnection(host="3.88.128.188", user="ciudadrenovablec_erp_usr", password="fJPh,o6Xo]!L", database="ciudadrenovablec_erp")
    db_conn.connect()

    # Proceso de registro de horas
    time_recorder = TimeRecorder(db_conn)
    
    # Actualiza los registros existentes
    today = datetime.today()
    period = PaymentPeriod(today)
    start_date, end_date = period.get_current_period()
    print(f"Start Date: {start_date}, End Date: {end_date}")
    time_recorder.update_records(start_date, today)

    # Registra los datos especiales
    time_recorder.register_special_data()

    # Cierre de la conexión
    db_conn.close()

if __name__ == "__main__":
    main()

