# SBMS Development Workflow

## Branch Strategy

```
main
  ├── service.md (spec)
  ├── README.md
  ├── PROJECT_STRUCTURE.md
  └── QUICK_START.md
  
  ├─→ android-apk (Z Fold 6 implementation)
  │    ├── build.gradle
  │    ├── src/main/java/com/oscyra/sbms/
  │    ├── src/main/res/
  │    ├── README-ANDROID.md
  │    └── proguard-rules.pro
  │
  └─→ E1310E-app (E1310E J2ME implementation)
       ├── build.xml
       ├── src/com/oscyra/sbms/
       ├── README-E1310E.md
       ├── COMPILATION.md
       └── TESTING.md
```

## Development Cycle

### Phase 1: Planning & Specification
1. Update service.md with technical details
2. Create feature branch from main
3. Design architecture
4. Document API contracts

### Phase 2: Implementation

**Android Development** (android-apk branch):
```bash
git checkout android-apk
# Make changes
git add .
git commit -m "Add Bluetooth connection pooling"
git push origin android-apk
```

**E1310E Development** (E1310E-app branch):
```bash
git checkout E1310E-app
# Make changes
git add .
git commit -m "Improve vCard parsing error handling"
git push origin E1310E-app
```

### Phase 3: Testing

**Android Tests**:
```bash
cd SBMS/android-apk
./gradlew test                    # Unit tests
./gradlew connectedAndroidTest    # Device tests
```

**E1310E Tests**:
```bash
cd SBMS/E1310E-app
ant clean jar
# Test with WTK emulator
/opt/WTK2.5.2/bin/emulator -Xdescriptor:dist/SBMS.jad
```

### Phase 4: Integration Testing

1. Build both APK and JAR
2. Deploy to actual devices
3. Test end-to-end message flow
4. Verify error handling
5. Performance benchmarking

### Phase 5: Release

```bash
# Create release tag on main
git checkout main
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Create release on GitHub with:
# - Release notes
# - SBMS-android.apk
# - SBMS.jar
# - SBMS.jad
```

## Code Review Process

### Android PR Review
1. Code style check (Google Java Style)
2. Unit test coverage (min 80%)
3. No ProGuard-breaking patterns
4. Bluetooth API correctness
5. Database migration safety

### E1310E PR Review
1. J2ME 1.4 compatibility
2. Memory footprint (<250KB heap)
3. No generics/1.5+ features
4. Battery efficiency
5. Bluetooth stack correctness

## Build Pipeline

### Local Build
```bash
# Android
cd android-apk
./gradlew clean build

# E1310E
cd E1310E-app
ant clean jar
```

### CI/CD (GitHub Actions)
```yaml
on: [push, pull_request]

jobs:
  android-build:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - setup-java
      - ./gradlew build
      - upload-artifact SBMS-android.apk

  e1310e-build:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - install-wtk
      - ant clean jar
      - upload-artifact SBMS.jar
```

## Common Tasks

### Adding a New Feature

```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Implement feature
# 3. Add tests
# 4. Update documentation
# 5. Commit with clear message
git commit -m "Add feature: description"

# 6. Push to appropriate branch
git push origin feature/new-feature
```

### Fixing a Bug

```bash
# 1. Create bugfix branch
git checkout -b bugfix/issue-123

# 2. Reproduce issue
# 3. Add test for bug
# 4. Fix implementation
# 5. Verify test passes
git commit -m "Fix issue #123: description"

# 6. Push
git push origin bugfix/issue-123
```

### Updating Documentation

```bash
# Make changes to .md files
git add *.md
git commit -m "Docs: update Bluetooth section"
git push origin main
```

## Testing Matrices

### Android Testing

**Devices**:
- Samsung Z Fold 6 (primary target)
- Samsung S24 Ultra (secondary)
- Pixel 9 Pro (baseline)

**Android Versions**:
- Android 12, 13, 14

**Test Cases**:
- [ ] App launch
- [ ] Bluetooth discovery
- [ ] Contact loading
- [ ] Message composition
- [ ] SMS sending
- [ ] Error handling
- [ ] Permission prompts

### E1310E Testing

**Emulator**:
- WTK 2.5.2 emulator

**Devices**:
- Samsung E1310E (primary)
- WTK generic MIDP 2.0

**Test Cases**:
- [ ] App launch
- [ ] Contact selection
- [ ] Message composition
- [ ] vCard generation
- [ ] Bluetooth transmission
- [ ] Error handling
- [ ] Memory usage

## Performance Monitoring

### Android Metrics
```bash
# Profile with Android Profiler
./gradlew profileDebug

# Metrics to monitor:
# - Bluetooth connection time
# - Memory usage
# - Battery consumption
# - Frame rate (UI responsiveness)
```

### E1310E Metrics
```bash
# Emulator heap monitoring
# WTK Device → Monitor → Heap

# Key metrics:
# - Max heap usage
# - GC frequency
# - Connection stability
```

## Release Checklist

- [ ] All tests passing
- [ ] Code review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped (semver)
- [ ] APK built and signed
- [ ] JAR preverified and tested
- [ ] Release notes written
- [ ] Tag created on main
- [ ] GitHub Release created
- [ ] Announce on channels

## Rollback Procedure

```bash
# If release has critical issues
git revert v1.0.0
git tag -a v1.0.1-hotfix -m "Rollback + fix"

# Or reset to previous version
git reset --hard v0.9.9
```

## Communication

### Status Updates
- Weekly in project README
- Monthly in GitHub Discussions
- Real-time in Issues

### Issues & PRs
- Label by component (android, e1310e, bluetooth, docs)
- Link related issues
- Reference service.md when applicable

## Tools & Resources

**Development**:
- Android Studio (Android)
- Eclipse IDE (E1310E)
- WTK 2.5.2 (J2ME testing)
- ProGuard (obfuscation)

**Version Control**:
- GitHub (repository)
- Git (local)
- GitHub Actions (CI/CD)

**Documentation**:
- Markdown (.md files)
- Javadoc (code comments)
- UML diagrams

**Testing**:
- JUnit (unit tests)
- Mockito (mocking)
- Espresso (UI testing)
- WTK Emulator

## Quick Links

- [Service Specification](service.md)
- [Android README](README-ANDROID.md)
- [E1310E README](README-E1310E.md)
- [Quick Start](QUICK_START.md)
- [GitHub Issues](https://github.com/CKCHDX/SBMS/issues)
- [GitHub Releases](https://github.com/CKCDHX/SBMS/releases)
