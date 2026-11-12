Name:		google-android-annotations
Version:	4.1.1.4
Release:	1
Summary:	Android platform lint annotations
Group:		Development/Java
License:	Apache-2.0
URL:		http://source.android.com/
# com.google.android:annotations 4.1.1.4. Two platform annotations, SuppressLint and TargetApi.
Source0:	google-android-annotations-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem

%description
com.google.android:annotations %{version}.
SuppressLint and TargetApi from the Android platform annotations library,
compiled from the upstream sources.

%prep
%autosetup -n google-android-annotations-%{version}
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
mkdir -p classes
find android -name '*.java' > sources.list
test "$(wc -l < sources.list)" -eq 2
javac --release 8 -Xlint:-options -d classes @sources.list
test -s classes/android/annotation/SuppressLint.class
test -s classes/android/annotation/TargetApi.class
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: android.annotation' > manifest.mf
jar cfm google-android-annotations.jar manifest.mf -C classes .
jar i google-android-annotations.jar
desc=$(jar --describe-module --file google-android-annotations.jar)
printf '%s\n' "$desc"
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	exit 1
fi
printf '%s\n' "$desc" | grep -F -qx 'android.annotation automatic'
cat > annotations.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.google.android</groupId>
  <artifactId>annotations</artifactId>
  <version>%{version}</version>
  <name>annotations</name>
  <description>Android platform lint annotations</description>
  <url>http://source.android.com/</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
</project>
END

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact annotations.pom:google-android-annotations.jar \
	--file-name google-android-annotations \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/com.google.android/annotations.sysjar"
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "annotations"' "$idx"
grep -F -q '/usr/share/java/google-android-annotations.jar' "$idx"
test -s %{buildroot}%{_javadir}/google-android-annotations.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
JAR=%{buildroot}%{_javadir}/google-android-annotations.jar
test -s "$JAR"
mkdir -p check
cat > check/Probe.java << 'EOF'
public class Probe {
    public static void main(String[] args) throws Exception {
        Class<?> type = Class.forName("android.annotation.SuppressLint");
        if (!type.isAnnotation()) {
            throw new RuntimeException("not annotation");
        }
        if (type.getMethod("value").getReturnType() != String[].class) {
            throw new RuntimeException("value");
        }
        Class<?> target = Class.forName("android.annotation.TargetApi");
        if (target.getMethod("value").getReturnType() != int.class) {
            throw new RuntimeException("target");
        }
        System.out.println("android_annotations_ok SuppressLint");
    }
}
EOF
javac --release 8 -Xlint:-options -cp "$JAR" -d check check/Probe.java
java -cp "check:$JAR" Probe > check/out.txt
cat check/out.txt
grep -F -qx 'android_annotations_ok SuppressLint' check/out.txt

%files -f .mfiles
%license LICENSE.txt
