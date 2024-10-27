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
    
    # Obtención del periodo actual
    today = datetime.today()
    period = PaymentPeriod(today)
    start_date, end_date = period.get_current_period()
    
    # Pregunta al usuario qué función desea ejecutar
    print("Seleccione una opción:")
    print("1. Actualizar registros de horas")
    print("2. Registrar datos especiales")
    choice = input("Ingrese el número de la opción (1 o 2): ")
    
    # Ejecuta la función seleccionada
    if choice == '1':
        time_recorder.update_records(start_date, today)
    elif choice == '2':
        time_recorder.register_special_data()
    else:
        print("Opción no válida. Por favor, elija 1 o 2.")
    
    # Cierre de la conexión
    db_conn.close()

if __name__ == "__main__":
    main()

