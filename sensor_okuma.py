import airsim 
import time 

# 1. BAĞLANTI VE KALKIŞ
print("Airsim'e bağlanılıyor...")
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)

print("Kalkış yapılıyor...")
client.takeoffAsync().join()

print("\n--- UYARI: GPS BAĞLANTISI YOK ---")
print("--- İÇ SENSÖRLER (IMU & ODOMETRİ) AKTİFLEŞTİRİLDİ ---\n")

# 2. SENSÖR VERİLERİNİ DÖNGÜ İLE OKUMA (10 saniye boyunca)
# DÖNGÜ 20 kez çalışacak, aralarda 0.5 sanıye bekleyecek
for i in range(20):
    # ODOMETRİ VERİSİ (Drone o an 3D düzlemde nerede?)
    durum = client.getMultirotorState()
    konum = durum.kinematics_estimated.position

    # IMU VERİSİ (Drone'un ivmesi ve kendi etrafındaki dönüş hızı nedir?)
    imu_verisi =client.getImuData(imu_name="", vehicle_name="")
    ivme = imu_verisi.linear_acceleration
    jiroskop = imu_verisi.angular_velocity

    print(f"--- [Veri Paketi {i+1}/20] ---")
    # Verileri virgülden sonra 2 basamak olacak şekilde (.2f) temizleyerek yazdırıyoruz.
    print(f"📍 YEREL KONUM -> X: {konum.x_val:.2f}, Y: {konum.y_val:.2f}, İrtifa (Z): {abs(konum.z_val):.2f}m")
    print(f"🚀 İVME (m/s^2)-> X: {ivme.x_val:.2f}, Y: {ivme.y_val:.2f}, Z: {ivme.z_val:2f}")
    print(f"🔄 JİROSKOP    -> X: {jiroskop.x_val:.2f}, Y: {jiroskop.y_val:.2f}, Z: {jiroskop.z_val:.2f}\n ")

    time.sleep(0.5)

# 3. İNİŞ VE GÜVENLİK 
print("Sensör okuma testi başarıyla tammalandı.İnişe geçiliyor...")
client.landAsync().join()
client.armDisarm(False)
client.enableApiControl(False)
print("Sistem güvenli duruma geçti. Görev Tamamlandı.")
