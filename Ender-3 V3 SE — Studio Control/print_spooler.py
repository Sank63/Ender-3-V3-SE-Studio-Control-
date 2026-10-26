import sys
import time
import re
import serial
import serial.tools.list_ports

DEFAULT_BAUDRATE = 115200

def select_serial_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("[-] COM-порты не найдены. Проверьте кабель USB-C.")
        sys.exit(1)

    print("\nДоступные порты:")
    for i, port in enumerate(ports):
        print(f"  [{i + 1}] {port.device} — {port.description}")

    if len(ports) == 1:
        print(f"[+] Автоматически выбран порт: {ports[0].device}")
        return ports[0].device

    choice = int(input(f"Выберите номер порта [1-{len(ports)}]: "))
    return ports[choice - 1].device

def clean_gcode_line(raw_line: str) -> str:
    return re.sub(r";.*$", "", raw_line).strip()

def emergency_stop(ser):
    print("\n[!] Аварийная остановка: отключаем нагрев и моторы...")
    try:
        ser.write(b"M104 S0\n")
        ser.write(b"M140 S0\n")
        ser.write(b"M84\n")
        time.sleep(0.5)
    except Exception:
        pass

def send_single_command(ser, cmd_text: str):
    """Отправляет одну команду и дожидается подтверждения 'ok'."""
    ser.write((cmd_text + "\n").encode("ascii"))
    while True:
        response = ser.readline().decode("ascii", errors="ignore").strip()
        if response.startswith("T:") or "echo:" in response:
            sys.stdout.write(f"\r[Статус] {response:<40}")
            sys.stdout.flush()
        if "ok" in response.lower():
            break

def send_gcode_file(port_name: str, file_path: str, baudrate: int = DEFAULT_BAUDRATE):
    print(f"[*] Чтение файла: {file_path}")
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        raw_lines = f.readlines()

    commands = [clean_gcode_line(l) for l in raw_lines if clean_gcode_line(l)]
    total_cmds = len(commands)
    print(f"[+] Загружено активных команд: {total_cmds}")

    print(f"[*] Подключение к {port_name}...")
    try:
        ser = serial.Serial(port=port_name, baudrate=baudrate, timeout=1.0)
    except serial.SerialException as e:
        print(f"[-] Ошибка порта: {e}")
        return

    print("[*] Инициализация принтера (3 секунды)...")
    time.sleep(3)
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    print("[+] Печать запущена!\n")
    start_time = time.time()
    last_percent = -1

    try:
        for idx, cmd in enumerate(commands, start=1):
            # 1. Расчет текущего прогресса
            current_percent = int((idx / total_cmds) * 100)

            # 2. Если процент изменился — отправляем команды на дисплей принтера
            if current_percent != last_percent:
                last_percent = current_percent
                send_single_command(ser, f"M117 Print {current_percent}%")
                send_single_command(ser, f"M73 P{current_percent}")

            # 3. Отправка строки из файла печати
            send_single_command(ser, cmd)

            # 4. Вывод данных в окно командной строки ПК
            elapsed = int(time.time() - start_time)
            m, s = divmod(elapsed, 60)
            sys.stdout.write(
                f"\rПрогресс: {current_percent:3d}% | Команда {idx}/{total_cmds} | Время: {m:02d}:{s:02d} | Тек: {cmd:<20}"
            )
            sys.stdout.flush()

        # Очистка статуса на дисплее по окончании печати
        send_single_command(ser, "M117 Print Complete!")
        print("\n\n[✓] Печать успешно завершена!")

    except KeyboardInterrupt:
        emergency_stop(ser)
        send_single_command(ser, "M117 Aborted")
        print("\n[-] Печать остановлена вручную.")
    finally:
        ser.close()
        print("[*] Соединение закрыто.")

if __name__ == "__main__":
    # Если файл перетащили на батник, путь передается аргументом sys.argv[1]
    if len(sys.argv) > 1:
        gcode_path = sys.argv[1].strip('"\'')
    else:
        gcode_path = input("Перетащите .gcode файл в консоль или введите путь: ").strip().strip('"\'')

    target_port = select_serial_port()
    send_gcode_file(target_port, gcode_path)