# 安装NFS

## 配置NFS服务器

### 创建NFS服务器，安装centos系统

### 配置yum软件源

```sh
sh yum-config.sh
```

### 安装存储管理工具

```sh
sh nfs-install-software.sh
```

### 配置NFS

```sh
sh nfs-config.sh
```

## 配置K8s的存储类

```sh
kubectl apply -f nfs-provisioner.yaml
kubectl apply -f nfs-storage-class.yaml
```

## 验证安装正确性

```sh
kubectl apply -f test-pvc.yaml
```