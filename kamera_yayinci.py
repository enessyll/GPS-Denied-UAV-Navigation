import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import airsim
import numpy as np
from cv_bridge import CvBridge
import subprocess

class AirSimKameraYayinci(Node):
    def __init__(self):
        super().__init__('kamera_yayinci_node')
        self.publisher_ = self.create_publisher(Image, '/airsim/kamera/goruntu', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.bridge = CvBridge()
        
        self.get_logger().info("Windows IP adresi bulunuyor...")
        # WSL2'den Windows IP'sini bulmanın en kesin yolu
        host_ip = subprocess.check_output("ip route show default | awk '{print $3}'", shell=True).decode('utf-8').strip()
        self.get_logger().info(f"Hedef Windows IP: {host_ip}")
        
        self.get_logger().info("AirSim'e bağlanılıyor (WSL'den Windows'a)...")
        # Localhost yerine doğrudan Windows'un IP adresine bağlanıyoruz
        self.client = airsim.MultirotorClient(ip=host_ip)
        self.client.confirmConnection()
        self.get_logger().info("Bağlantı Başarılı! ROS 2 Görüntü yayını başlıyor...")

    def timer_callback(self):
        responses = self.client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)])
        response = responses[0]
        
        if response.image_data_uint8 != b'':
            img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
            img_rgb = img1d.reshape(response.height, response.width, 3)
            ros_image = self.bridge.cv2_to_imgmsg(img_rgb, encoding="bgr8")
            self.publisher_.publish(ros_image)

def main(args=None):
    rclpy.init(args=args)
    dugum = AirSimKameraYayinci()
    rclpy.spin(dugum)
    dugum.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()