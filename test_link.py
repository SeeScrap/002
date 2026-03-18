import serial
import serial.tools.list_ports
import time

def find_esp32_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        print(f"Found port: {port.device} - {port.description}")
        if "USB" in port.description or "ttyACM" in port.device or "CH340" in port.description:
            return port.device
    return None

def main():
    print("Finding ESP32...")
    port = find_esp32_port()
    
    if not port:
        print("❌ ESP32 not found. Please check USB connection.")
        return

    print(f"✅ ESP32 found at {port}. Connecting...")
    
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        time.sleep(2) # Wait for reset
        
        print("\n--- Test 1: Get Temp/Humid ---")
        ser.write(b"get_temp_all\n")
        time.sleep(0.5)
        
        start = time.time()
        while time.time() - start < 2:
            if ser.in_waiting:
                print(f"RX: {ser.readline().decode().strip()}")
                
        print("\n--- Test 2: Get Soil ---")
        ser.write(b"get_soil\n")
        time.sleep(0.5)
        
        start = time.time()
        while time.time() - start < 2:
            if ser.in_waiting:
                print(f"RX: {ser.readline().decode().strip()}")

        print("\n--- Test 3: Get Light (BH1750) ---")
        ser.write(b"get_light\n")
        time.sleep(0.5)
        
        start = time.time()
        while time.time() - start < 2:
            if ser.in_waiting:
                print(f"RX: {ser.readline().decode().strip()}")

        print("\n✅ Sensor Verification Finished.")

        print("\n--- Test 4: Relays (Click Test) ---")
        for i in range(1, 9):
            print(f"Testing Relay {i} ON...")
            ser.write(f"relay_on {i}\n".encode())
            time.sleep(0.5)
            print(f"Testing Relay {i} OFF...")
            ser.write(f"relay_off {i}\n".encode())
            time.sleep(0.5)

        print("\n✅ Relay Test Finished.")
        ser.close()

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()
