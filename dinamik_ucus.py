import airsim
import time

# 1. BAĞLANTI VE KALKIŞ
print("AirSim'e bağlanılıyor...")
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)

print("Kalkış yapılıyor...")
client.takeoffAsync().join()

# 2. DİNAMİK UÇUŞ KOMUTU (Sır Burada: Sonunda .join() YOK!)
print("\n--- Hedefe doğru hareket başlıyor (Asenkron Uçuş) ---")
# Drone X:30, Y:0, Z:-3 noktasına 4m/s hızla gitmeye başlar ve kod alt satıra geçer.
client.moveToPositionAsync(30, 0, -3, 4)

# 3. HAREKET HALİNDEYKEN CANLI SENSÖR OKUMA
print("--- Uçuş sırasında canlı sensör verileri alınıyor ---\n")

# Dron uçarken yaklaşık 8 saniye boyunca hem konumunu hem ivmesini anlık basacak
for i in range(16): 
    durum = client.getMultirotorState()
    konum = durum.kinematics_estimated.position
    
    imu_verisi = client.getImuData(imu_name="", vehicle_name="")
    ivme = imu_verisi.linear_acceleration
    
    # Ekrana hareket halindeki değişimi yazdırıyoruz
    print(f"✈️ UÇUŞTA -> Mesafe X: {konum.x_val:.2f}m | İrtifa: {abs(konum.z_val):.2f}m | 🚀 İVME Z: {ivme.z_val:.2f}")
    time.sleep(0.5)

# 4. İNİŞ VE GÜVENLİK
print("\nUçuş ve okuma tamamlandı. İnişe geçiliyor...")
client.landAsync().join()
client.armDisarm(False)
client.enableApiControl(False)
print("Sistem güvenli duruma geçti. Görev Tamamlandı!")