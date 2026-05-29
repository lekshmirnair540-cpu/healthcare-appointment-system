import pymysql
import sys

try:
    # Connect to MySQL
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='Newroot123',
        database='healthcare_db'
    )
    
    cursor = conn.cursor()
    
    # Create doctor table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctor (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            specialization VARCHAR(100) NOT NULL,
            qualification VARCHAR(200),
            experience INT,
            fee DECIMAL(10,2),
            available_days VARCHAR(200),
            available_time_slots VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] Doctor table ready")
    
    # Check existing doctors
    cursor.execute("SELECT COUNT(*) FROM doctor")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Insert doctors
        doctors = [
            ('Dr. Sarah Johnson', 'Cardiologist', 'MD, FACC', 12, 1500, 'Mon,Tue,Wed,Fri', '10:00-13:00,15:00-18:00'),
            ('Dr. Michael Chen', 'Dermatologist', 'MD, FAAD', 8, 1200, 'Mon,Wed,Thu,Sat', '09:00-12:00,14:00-17:00'),
            ('Dr. Priya Sharma', 'Pediatrician', 'MD, FAAP', 10, 1000, 'Tue,Thu,Fri,Sat', '11:00-14:00,16:00-19:00'),
            ('Dr. James Wilson', 'Orthopedic', 'MS, DNB', 15, 1800, 'Mon,Tue,Thu,Fri', '09:00-12:00,15:00-18:00'),
            ('Dr. Emily Brown', 'Neurologist', 'DM, FRCP', 14, 2000, 'Mon,Wed,Fri,Sat', '10:00-13:00,14:00-17:00')
        ]
        
        for doc in doctors:
            cursor.execute("""
                INSERT INTO doctor (name, specialization, qualification, experience, fee, available_days, available_time_slots)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, doc)
        
        conn.commit()
        print(f"[OK] Added {len(doctors)} doctors")
    else:
        print(f"[OK] Doctors already exist ({count} doctors)")
    
    # Show doctors
    cursor.execute("SELECT id, name, specialization, fee FROM doctor")
    print("\nDoctor List:")
    for row in cursor.fetchall():
        print(f"  ID:{row[0]} | {row[1]} | {row[2]} | Rs.{row[3]}")
    
    cursor.close()
    conn.close()
    print("\n[DONE] Setup complete!")
    
except Exception as e:
    print(f"[ERROR] {e}")
    
input("\nPress Enter to exit...")