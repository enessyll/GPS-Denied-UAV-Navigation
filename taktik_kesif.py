import airsim
import time

# 1. BAĞLANTI VE KALKIŞ
print("AirSim'e bağlanılıyor... (GPS-Denied Mod Aktif)")
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)

print("Kalkış yapılıyor...")
client.takeoffAsync().join()

# 2. GÖREV PARAMETRELERİ
z_irtifa = -6.0  # Daha yüksekten uçalım (6 metre)
hiz = 8          # Mesafeler uzak olduğu için hızı 8 m/s yaptık
dosya_adi = "taktik_kesif_logu.txt"

# 3. ÖZEL GÖREV FONKSİYONLARI (Kendi komutlarımızı yaratıyoruz)
def etrafinda_don():
    print("🔄 360 Derece Keşif Dönüşü Yapılıyor...")
    # Saniyede 90 derece dönerek 4 saniyede kendi etrafında tam tur atar
    client.moveByVelocityZAsync(0, 0, z_irtifa, 4, airsim.DrivetrainType.MaxDegreeOfFreedom, airsim.YawMode(True, 90)).join()

def sensor_taramasi_ve_kayit(nokta_adi, durum_mesaji, log_dosyasi):
    durum = client.getMultirotorState()
    x_val = durum.kinematics_estimated.position.x_val
    y_val = durum.kinematics_estimated.position.y_val
    
    imu = client.getImuData(imu_name="", vehicle_name="")
    z_ivme = imu.linear_acceleration.z_val
    
    # Ekrana ve TXT dosyasına anlık durum basıyoruz
    print(f"📡 Sensör Tarama: X:{x_val:.1f} Y:{y_val:.1f} | Durum: {durum_mesaji}")
    log_dosyasi.write(f"{nokta_adi}, {durum_mesaji}, {x_val:.1f}, {y_val:.1f}, {z_ivme:.2f}\n")

# 4. TAKTİK KEŞİF GÖREVİ (Dosyayı yazma modunda açarak başlatıyoruz)
with open(dosya_adi, "w", encoding="utf-8") as dosya:
    dosya.write("Nokta, Durum_Raporu, X_Konum, Y_Konum, Z_Ivme\n")
    print("\n--- TAKTİK KEŞİF GÖREVİ BAŞLADI ---")

    # A NOKTASI
    print("\n🚀 [A NOKTASINA İNTİKAL EDİLİYOR]")
    client.moveToPositionAsync(50, 0, z_irtifa, hiz).join()
    etrafinda_don()
    sensor_taramasi_ve_kayit("A Noktasi", "A Noktasi Temiz", dosya)
    print("✅ Rapor: A Noktası Temiz.")

    # B NOKTASI
    print("\n🚀 [B NOKTASINA İNTİKAL EDİLİYOR]")
    client.moveToPositionAsync(50, 50, z_irtifa, hiz).join()
    etrafinda_don()
    sensor_taramasi_ve_kayit("B Noktasi", "B Noktasi Temiz", dosya)
    print("✅ Rapor: B Noktası Temiz.")

    # C NOKTASI
    print("\n🚀 [C NOKTASINA İNTİKAL EDİLİYOR]")
    client.moveToPositionAsync(-30, 50, z_irtifa, hiz).join()
    etrafinda_don()
    sensor_taramasi_ve_kayit("C Noktasi", "TEHLIKE ALGILANDI", dosya)
    print("⚠️ UYARI: C Noktasında TEHLİKE ALGILANDI! Acil manevra yapılıyor.")

    # D NOKTASI
    print("\n🚀 [D NOKTASINA İNTİKAL EDİLİYOR]")
    client.moveToPositionAsync(-30, -30, z_irtifa, hiz).join()
    etrafinda_don()
    sensor_taramasi_ve_kayit("D Noktasi", "2 Yabanci Cisim", dosya)
    print("🚨 KIRMIZI KOD: 2 Yabancı Cisim Algılandı! Merkeze (A Noktasına) dönülüyor.")

    # A NOKTASINA GERİ DÖNÜŞ
    print("\n🚀 [A NOKTASINA DÖNÜŞ BAŞLADI]")
    client.moveToPositionAsync(50, 0, z_irtifa, hiz).join()
    print("✅ Rapor: A Noktasına güvenli dönüş sağlandı.")

    # BAŞLANGIÇ NOKTASINA (HOME) İNİŞ
    print("\n🚀 [BAŞLANGIÇ NOKTASINA (0,0) DÖNÜLÜYOR]")
    client.moveToPositionAsync(0, 0, -2, hiz).join()

# 5. İNİŞ VE KAPANIŞ
print("\nGörev kusursuz tamamlandı. İnişe geçiliyor...")
client.landAsync().join()
client.armDisarm(False)
client.enableApiControl(False)
print(f"Sistem kapandı. Tüm görev uçuş veri kayıtları '{dosya_adi}' dosyasına işlendi.")