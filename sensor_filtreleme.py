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

# Dronu asenkron olarak ileri sürüyoruz ki ivme dalgalansın
client.moveToPositionAsync(30, 0, -3, 4)

print("\n--- SENSÖR GÜRÜLTÜ FİLTRELEME (HAREKETLİ ORTALAMA) ---")

# 2. FİLTRE ALGORİTMASI İÇİN BOŞ LİSTE
z_ivme_gecmisi = []
filtre_boyutu = 5  # Son 5 verinin ortalamasını alacağız

for i in range(25):
    # IMU'dan anlık ham veriyi çekiyoruz
    imu_verisi = client.getImuData(imu_name="", vehicle_name="")
    ham_z = imu_verisi.linear_acceleration.z_val
    
    # Yeni veriyi listemizin sonuna ekliyoruz (append)
    z_ivme_gecmisi.append(ham_z)
    
    # Eğer listemizdeki veri sayısı 5'i geçerse, en eski veriyi (0. indeks) siliyoruz (pop)
    if len(z_ivme_gecmisi) > filtre_boyutu:
        z_ivme_gecmisi.pop(0)
        
    # Listedeki mevcut verilerin toplamını, eleman sayısına bölerek ortalamayı buluyoruz
    filtrelenmis_z = sum(z_ivme_gecmisi) / len(z_ivme_gecmisi)
    
    # Ekranda Ham veri ile Filtrelenmiş veriyi yan yana kıyaslıyoruz
    print(f"[{i+1}/25] 💥 HAM İVME: {ham_z:.2f}  |  🛡️ FİLTRELENMİŞ: {filtrelenmis_z:.2f}")
    
    time.sleep(0.3)

# 3. İNİŞ
print("\nFiltreleme testi tamamlandı. İnişe geçiliyor...")
client.landAsync().join()
client.armDisarm(False)
client.enableApiControl(False)
print("Sistem güvenli duruma geçti.")