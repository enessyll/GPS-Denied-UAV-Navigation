import airsim
import time

# 1. BAĞLANTI VE KALKIŞ
print("AirSim'e bağlanılıyor...")
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)

print("Kalkış yapılıyor... (Yerel Odometri Aktif, GPS Devre Dışı)")
client.takeoffAsync().join()

# 2. GPS-DENIED (GPS OLMADAN) YEREL ROTA İŞARETLEMESİ
# Z değerleri düşürüldü (-2.5, -3 vb.). Dron yere daha yakın, sinematik ve stabil uçacak.
rota_noktalari = [
    {"isim": "A Noktasi", "x": 15, "y": 0,  "z": -2.5, "hiz": 3},
    {"isim": "B Noktasi", "x": 15, "y": 15, "z": -3.0, "hiz": 3}, 
    {"isim": "C Noktasi", "x": -5, "y": 15, "z": -3.0, "hiz": 3},
    {"isim": "D Noktasi", "x": -5, "y": -5, "z": -2.0, "hiz": 3},  
    {"isim": "A Noktasina Donus", "x": 15, "y": 0, "z": -2.5, "hiz": 4} # Kapalı döngü: Tekrar A'ya dönüş
]

print("\n--- SİSTEM UYARISI: UYDU BAĞLANTISI (GPS) YOK ---")
print("--- İÇ SENSÖRLER (ODOMETRİ) İLE OTONOM UÇUŞ BAŞLIYOR ---")

# 3. ROTAYI DÖNGÜ İLE TAKİP ETME
for nokta in rota_noktalari:
    print(f"\nHedef: {nokta['isim']} rotasına gidiliyor...")
    print(f"Yerel Koordinat -> X: {nokta['x']}, Y: {nokta['y']}, İrtifa: {abs(nokta['z'])}m")
    
    # moveToPositionAsync komutu Global GPS ile değil, dronun kalktığı 0,0 noktasını referans alarak çalışır.
    client.moveToPositionAsync(nokta['x'], nokta['y'], nokta['z'], nokta['hiz']).join()
    
    print(f">>> {nokta['isim']} noktasına başarıyla ulaşıldı! <<<")
    time.sleep(1.0) 

# 4. BAŞLANGIÇ NOKTASINA DÖNÜŞ VE İNİŞ
print("\nTüm görev noktaları gezildi. Kalkış merkezine (Home) dönülüyor...")
client.moveToPositionAsync(0, 0, -1.5, 3).join() 

print("İnişe geçiliyor...")
client.landAsync().join()
client.armDisarm(False)
client.enableApiControl(False)
print("Sistem güvenli duruma geçti. Görev Tamamlandı.")