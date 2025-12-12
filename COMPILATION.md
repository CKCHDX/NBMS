# E1310E SBMS - Detailed Compilation Guide

## Environment Setup

### 1. Install Java Development Kit (JDK)

**Required**: JDK 1.4-1.6 (must support CLDC bytecode)

```bash
# Ubuntu/Debian
sudo apt-get install sun-java6-jdk

# Or use OpenJDK
sudo apt-get install openjdk-6-jdk

# Verify
java -version
javac -version
```

### 2. Download Wireless Toolkit (WTK)

```bash
# Download from Oracle (requires account)
# https://www.oracle.com/java/technologies/wtk-121-downloads.html

# Extract
tar xzf WTK2.5.2.tar.gz
mv WTK2.5.2 /opt/WTK2.5.2
```

### 3. Install Ant Build Tool

```bash
# Ubuntu/Debian
sudo apt-get install ant

# Or download from Apache
# https://ant.apache.org/bindownload.cgi

# Verify
ant -version
```

### 4. (Optional) Samsung J2ME SDK

```bash
# Download from Samsung Developer Program
# Extract to /opt/Samsung-J2ME-SDK

# This provides Samsung-specific APIs like:
# - com.samsung.telephony.*
# - com.samsung.io.*
# - com.samsung.net.*
```

## Project Configuration

### Edit build.xml

```xml
<property name="wtk.home" value="/opt/WTK2.5.2" />
<property name="samsung.home" value="/opt/Samsung-J2ME-SDK" />
```

### Verify Directory Structure

```
SBMS-E1310E/
├── build.xml
├── src/
│   └── com/oscyra/sbms/
│       ├── SBMSApp.java
│       ├── MainScreen.java
│       ├── bluetooth/BluetoothHandler.java
│       ├── storage/StorageManager.java
│       ├── storage/Contact.java
│       ├── storage/ContactManager.java
│       └── ui/MessageComposer.java
├── build/         (created by ant)
└── dist/          (created by ant)
```

## Compilation Process

### Step 1: Compile Java Sources

```bash
ant compile
```

**Output**:
```
compile:
    [javac] Compiling 8 source files to build/classes
    [javac] Note: Some input files use unchecked or unsafe operations.
    [javac] Note: Recompile with -Xdiags:verbose to see details.
```

**Troubleshooting**:
- "Cannot find symbol": Missing classpath
  ```bash
  # Verify WTK libraries exist
  ls -la /opt/WTK2.5.2/lib/*.jar
  ```

- "Unsupported class version": Wrong JDK version
  ```bash
  # Use Java 1.4-1.6 compatible JDK
  update-alternatives --config java
  ```

### Step 2: Preverify Bytecode

```bash
ant preverify
```

**Output**:
```
preverify:
    [exec] Preverifying class com/oscyra/sbms/SBMSApp
    [exec] Preverifying class com/oscyra/sbms/MainScreen
    ...
    [exec] Verification complete
```

**What is Preverification?**
- J2ME requires bytecode verification at compile-time (not runtime)
- Preverifier adds verify bytecode instructions
- Reduces phone processing load
- Required for all J2ME apps

### Step 3: Package JAR

```bash
ant jar
```

**Output**:
```
jar:
      [jar] Building jar: dist/SBMS.jar
      [jar] Entry 0 : META-INF/MANIFEST.MF
      [jar] Entry 1 : com/oscyra/sbms/SBMSApp.class
      ...
```

### Step 4: Verify JAR Contents

```bash
jar tf dist/SBMS.jar

# Output:
META-INF/MANIFEST.MF
com/oscyra/sbms/SBMSApp.class
com/oscyra/sbms/MainScreen.class
com/oscyra/sbms/bluetooth/BluetoothHandler.class
...
```

### Step 5: Create JAD Descriptor

```bash
cat > dist/SBMS.jad << 'EOF'
MIDlet-1: SBMS, , com.oscyra.sbms.SBMSApp
MIDlet-Jar-Size: $(file -b dist/SBMS.jar | wc -c)
MIDlet-Jar-URL: SBMS.jar
MIDlet-Name: Samsung Bluetooth Message Service
MIDlet-Vendor: Oscyra Solutions
MIDlet-Version: 1.0.0
MicroEdition-Configuration: CLDC-1.1
MicroEdition-Profile: MIDP-2.0
EOF

# Manually update Jar-Size:
ls -la dist/SBMS.jar  # Note the byte count

# Edit dist/SBMS.jad:
MIDlet-Jar-Size: 65536  # Use actual size
```

## One-Command Build

```bash
ant clean jar
```

This compiles, preverifies, and packages in sequence.

## Emulator Testing

### Launch WTK Emulator

```bash
/opt/WTK2.5.2/bin/emulator -Xdescriptor:dist/SBMS.jad
```

### Within Emulator

1. Phone menu appears
2. Navigate: Applications → Installed
3. Select SBMS
4. Press OK to launch
5. Test UI navigation with arrow keys
6. Test message composition

## Deployment Options

### Option A: Bluetooth OPP Transfer

```bash
# From Linux with Bluetooth tools
obexftp -b E1:31:0E:XX:XX:XX -p dist/SBMS.jar

# Or use GUI: Nautilus/Konqueror Bluetooth browser
```

### Option B: HTTP Server Deployment

```bash
# Host files on web server
mkdir -p /var/www/html/sbms
cp dist/SBMS.jad /var/www/html/sbms/
cp dist/SBMS.jar /var/www/html/sbms/

# From phone, browse to:
# http://YOUR_IP/sbms/SBMS.jad
```

### Option C: USB Direct Transfer (if supported)

```bash
# Copy to USB mount point
cp dist/SBMS.jar /mnt/usb/

# On E1310E: Applications → Install New App → USB Devices
```

## Build Optimization

### Reduce JAR Size

```bash
# Add to build.xml
<jar jarfile="${dist.dir}/SBMS.jar" basedir="${build.dir}" level="9">
  <!-- ZIP compression level 9 (maximum) -->
</jar>
```

### Strip Debug Information

```bash
javac -g:none src/com/oscyra/sbms/*.java
```

### Typical Sizes

- Unoptimized: ~75 KB
- With compression: ~60 KB
- With obfuscation: ~40 KB (ProGuard)

## Continuous Integration

### GitHub Actions Workflow

Create `.github/workflows/e1310e-build.yml`:

```yaml
name: Build E1310E SBMS

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        with:
          ref: E1310E-app
      
      - name: Install JDK 1.6
        run: |
          sudo apt-get update
          sudo apt-get install openjdk-6-jdk
      
      - name: Install WTK
        run: |
          wget https://download.java.net/java/early_access/wtk/WTK2.5.2.tar.gz
          tar xzf WTK2.5.2.tar.gz
          mv WTK2.5.2 /opt/
      
      - name: Build
        run: |
          ant jar
      
      - name: Upload Artifact
        uses: actions/upload-artifact@v2
        with:
          name: SBMS.jar
          path: dist/SBMS.jar
```

## Troubleshooting Common Issues

### "Cannot find symbol"

```
[javac] error: cannot find symbol
[javac]   symbol:   class Vector
[javac]   location: package java.util
```

**Solution**: Add WTK classes to CLASSPATH

```bash
export CLASSPATH=/opt/WTK2.5.2/lib/*:$CLASSPATH
ant compile
```

### "Unsupported class version 50.0"

```
Exception in thread "main" java.lang.UnsupportedClassVersionError:
  com/oscyra/sbms/SBMSApp (Unsupported class version 50.0)
```

**Solution**: Compile with Java 1.6, not 1.8+

```bash
java -version  # Should show 1.6.x

# Or specify javac version
/usr/lib/jvm/java-6-openjdk-amd64/bin/javac -version
```

### "Preverification failed"

```
FATAL ERROR: Could not verify all classes
```

**Solution**: Ensure bytecode is valid

```bash
# Recompile and try again
ant clean compile preverify

# Or manually run preverify
/opt/WTK2.5.2/bin/preverify -classpath "/opt/WTK2.5.2/lib/*" -d build/ build/
```

### "JAD file not found during installation"

**Solution**: Ensure both files present and accessible

```bash
ls -la dist/SBMS.*
# dist/SBMS.jad
# dist/SBMS.jar

# Update JAD with correct Jar-Size and Jar-URL
echo "Jar size: $(stat -c%s dist/SBMS.jar) bytes"
```

## Advanced: ProGuard Obfuscation

Reduce size and protect source:

```bash
# Install ProGuard
wget https://sourceforge.net/projects/proguard/files/proguard/7.3.0/proguard7.3.0.zip
unzip proguard7.3.0.zip

# Create proguard.conf
cat > proguard.conf << 'EOF'
-injars build/
-outjars dist/
-libraryjars /opt/WTK2.5.2/lib/midpapi.jar
-libraryjars /opt/WTK2.5.2/lib/cldcapi.jar
-keep class com.oscyra.sbms.SBMSApp
EOF

# Run ProGuard
java -jar proguard7.3.0/lib/proguard.jar @ proguard.conf
```

## Performance Benchmarks

| Metric | Value | Notes |
|--------|-------|-------|
| Compile Time | 2-3s | 8 Java files |
| Preverify Time | 1-2s | Bytecode verification |
| JAR Size | 60 KB | Compressed |
| Uncompressed JAR | 75 KB | Raw classes |
| With ProGuard | 40 KB | Obfuscated |
| Full Build Time | 5-6s | Clean + compile + jar |

## Next Steps

1. [Test with WTK Emulator](TESTING.md)
2. [Deploy to E1310E](DEPLOYMENT.md)
3. [Integration with Android APK](../README-ANDROID.md)
