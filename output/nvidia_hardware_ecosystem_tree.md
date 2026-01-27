# NVIDIA 硬件生态系统树状图 / NVIDIA Hardware Ecosystem Tree

> 基于 10,000 页面爬取分析结果生成
> Generated: 2026-01-27

## 完整硬件生态思维导图

```mermaid
mindmap
  root((NVIDIA Hardware Ecosystem))
    Consumer_GPU[消费级 GPU]
      GeForce_50[GeForce RTX 50 系列]
        RTX_5090[RTX 5090]
        RTX_5080[RTX 5080]
        RTX_5070_Ti[RTX 5070 Ti]
        RTX_5070[RTX 5070]
        RTX_5060_Ti[RTX 5060 Ti]
        RTX_5060[RTX 5060]
      GeForce_40[GeForce RTX 40 系列]
        RTX_4090[RTX 4090]
        RTX_4080_Super[RTX 4080 Super]
        RTX_4080[RTX 4080]
        RTX_4070_Ti_Super[RTX 4070 Ti Super]
        RTX_4070_Ti[RTX 4070 Ti]
        RTX_4070[RTX 4070]
        RTX_4060_Ti[RTX 4060 Ti]
        RTX_4060[RTX 4060]
      GeForce_30[GeForce RTX 30 系列]
        RTX_3090_Ti[RTX 3090 Ti]
        RTX_3090[RTX 3090]
        RTX_3080_Ti[RTX 3080 Ti]
        RTX_3080[RTX 3080]
        RTX_3070_Ti[RTX 3070 Ti]
        RTX_3070[RTX 3070]
        RTX_3060_Ti[RTX 3060 Ti]
        RTX_3060[RTX 3060]
      GeForce_Legacy[历史系列]
        GTX_16[GTX 16 系列]
        GTX_10[GTX 10 系列]
    
    Datacenter_GPU[数据中心 GPU]
      Blackwell[Blackwell 架构]
        B200[B200]
        B100[B100]
        GB200[GB200 NVL72]
      Hopper[Hopper 架构]
        H200[H200]
        H100[H100 SXM/PCIe]
        H100_NVL[H100 NVL]
      Ada_Lovelace[Ada Lovelace]
        L40S[L40S]
        L40[L40]
        L4[L4]
      Ampere[Ampere 架构]
        A100[A100 SXM/PCIe]
        A30[A30]
        A10[A10]
        A2[A2]
    
    Professional_GPU[专业级 GPU]
      RTX_Pro[RTX 专业系列]
        RTX_6000_Ada[RTX 6000 Ada]
        RTX_5000_Ada[RTX 5000 Ada]
        RTX_4500_Ada[RTX 4500 Ada]
        RTX_4000_Ada[RTX 4000 Ada]
      Quadro[Quadro 系列]
        Quadro_RTX_8000[Quadro RTX 8000]
        Quadro_RTX_6000[Quadro RTX 6000]
        Quadro_RTX_5000[Quadro RTX 5000]
        Quadro_RTX_4000[Quadro RTX 4000]
    
    DGX_Systems[DGX 系统]
      DGX_SuperPOD[DGX SuperPOD]
        GB200_NVL72[GB200 NVL72 机架]
        H100_SuperPOD[H100 SuperPOD]
      DGX_B200[DGX B200]
      DGX_H100[DGX H100]
      DGX_Station[DGX Station]
      DGX_Cloud[DGX Cloud]
    
    HGX_Platform[HGX 平台]
      HGX_B200[HGX B200]
      HGX_H200[HGX H200]
      HGX_H100[HGX H100]
      HGX_A100[HGX A100]
    
    Edge_Embedded[边缘计算与嵌入式]
      Jetson[Jetson 系列]
        Jetson_Thor[Jetson Thor]
        Jetson_AGX_Orin[Jetson AGX Orin]
        Jetson_Orin_NX[Jetson Orin NX]
        Jetson_Orin_Nano[Jetson Orin Nano]
        Jetson_Xavier[Jetson Xavier]
        Jetson_Nano[Jetson Nano]
      IGX[IGX 工业边缘]
        IGX_Orin[IGX Orin]
      EGX[EGX 企业边缘]
    
    Automotive[汽车平台]
      DRIVE_Platform[DRIVE 平台]
        DRIVE_Thor[DRIVE Thor]
        DRIVE_Orin[DRIVE Orin]
        DRIVE_AGX[DRIVE AGX]
      DRIVE_Hyperion[DRIVE Hyperion]
      DRIVE_Sim[DRIVE Sim]
    
    Networking[网络产品]
      DPU[数据处理单元]
        BlueField_4[BlueField-4]
        BlueField_3[BlueField-3]
        BlueField_2[BlueField-2]
      InfiniBand[InfiniBand]
        ConnectX_8[ConnectX-8]
        ConnectX_7[ConnectX-7]
        Quantum_2[Quantum-2 交换机]
      Ethernet[以太网]
        Spectrum_X[Spectrum-X]
        Spectrum_4[Spectrum-4]
        SuperNIC[SuperNIC]
    
    Grace_CPU[Grace CPU]
      Grace_Hopper[Grace Hopper 超级芯片]
      Grace_Blackwell[Grace Blackwell]
      Grace_CPU_Only[Grace CPU]
```

## 硬件产品线层次结构

```mermaid
flowchart TD
    subgraph Consumer[消费级市场]
        GeForce[GeForce 系列]
        Shield[SHIELD 设备]
    end
    
    subgraph Professional[专业级市场]
        RTX_Pro[RTX 专业系列]
        Quadro[Quadro]
        Studio[NVIDIA Studio]
    end
    
    subgraph Datacenter[数据中心]
        DC_GPU[数据中心 GPU]
        DGX[DGX 系统]
        HGX[HGX 平台]
        Grace[Grace CPU]
    end
    
    subgraph Edge[边缘计算]
        Jetson[Jetson]
        IGX[IGX]
        EGX[EGX]
    end
    
    subgraph Automotive[汽车]
        DRIVE[DRIVE 平台]
        AV[自动驾驶系统]
    end
    
    subgraph Networking[网络]
        DPU[BlueField DPU]
        IB[InfiniBand]
        Eth[Ethernet]
    end
    
    NVIDIA((NVIDIA)) --> Consumer
    NVIDIA --> Professional
    NVIDIA --> Datacenter
    NVIDIA --> Edge
    NVIDIA --> Automotive
    NVIDIA --> Networking
```

## GPU 架构演进

```mermaid
flowchart LR
    subgraph 2020_2021[2020-2021]
        Ampere[Ampere 架构]
    end
    
    subgraph 2022_2023[2022-2023]
        Hopper[Hopper 架构]
        Ada[Ada Lovelace]
    end
    
    subgraph 2024_2025[2024-2025]
        Blackwell[Blackwell 架构]
    end
    
    subgraph 2025_2026[2025-2026]
        Rubin[Rubin 架构]
    end
    
    Ampere --> Hopper
    Ampere --> Ada
    Hopper --> Blackwell
    Ada --> Blackwell
    Blackwell --> Rubin
```

## 硬件生态分类统计

```mermaid
pie title "NVIDIA 硬件产品分布"
    "消费级 GPU (GeForce)" : 383
    "专业级 GPU" : 45
    "数据中心 GPU" : 32
    "网络产品" : 38
    "Jetson 嵌入式" : 24
    "汽车平台 (DRIVE)" : 19
    "DGX 系统" : 12
```

## 详细产品分类表格

### 1. 数据中心 GPU

| 架构 | 型号 | 显存 | 主要用途 |
|------|------|------|----------|
| **Blackwell** | B200 | 192GB HBM3e | AI 训练/推理 |
| | B100 | 192GB HBM3e | AI 训练/推理 |
| | GB200 NVL72 | 13.5TB | 超大规模 AI |
| **Hopper** | H200 | 141GB HBM3e | AI 训练/推理 |
| | H100 SXM | 80GB HBM3 | AI 训练 |
| | H100 PCIe | 80GB HBM3 | AI 推理 |
| **Ada** | L40S | 48GB GDDR6 | AI 推理/图形 |
| | L40 | 48GB GDDR6 | AI 推理 |
| | L4 | 24GB GDDR6 | 视频/AI 推理 |
| **Ampere** | A100 | 80/40GB HBM2e | AI 训练/HPC |
| | A30 | 24GB HBM2 | 推理 |
| | A10 | 24GB GDDR6 | 推理/图形 |

### 2. 消费级 GPU (GeForce)

| 系列 | 型号 | 架构 | 显存 |
|------|------|------|------|
| **RTX 50** | 5090 | Blackwell | 32GB GDDR7 |
| | 5080 | Blackwell | 16GB GDDR7 |
| | 5070 Ti | Blackwell | 16GB GDDR7 |
| | 5070 | Blackwell | 12GB GDDR7 |
| **RTX 40** | 4090 | Ada | 24GB GDDR6X |
| | 4080 Super | Ada | 16GB GDDR6X |
| | 4070 Ti Super | Ada | 16GB GDDR6X |
| | 4060 Ti | Ada | 16/8GB GDDR6 |
| **RTX 30** | 3090 Ti | Ampere | 24GB GDDR6X |
| | 3080 Ti | Ampere | 12GB GDDR6X |
| | 3070 | Ampere | 8GB GDDR6 |

### 3. DGX 系统

| 系统 | GPU 配置 | 总显存 | 用途 |
|------|----------|--------|------|
| **DGX B200** | 8x B200 | 1.5TB | AI 超算 |
| **DGX H100** | 8x H100 | 640GB | AI 训练 |
| **DGX Station** | 4x GPU | 可变 | 工作站 |
| **DGX SuperPOD** | 多机架 | PB 级 | 超大规模 |
| **DGX Cloud** | 云服务 | 按需 | AI 即服务 |

### 4. Jetson 嵌入式

| 型号 | SoC | 算力 | 应用场景 |
|------|-----|------|----------|
| **AGX Thor** | Thor | 2000 TOPS | 自动驾驶/机器人 |
| **AGX Orin** | Orin | 275 TOPS | 高端边缘 AI |
| **Orin NX** | Orin | 100 TOPS | 中端边缘 AI |
| **Orin Nano** | Orin | 40 TOPS | 入门边缘 AI |
| **Xavier NX** | Xavier | 21 TOPS | 紧凑边缘 |
| **Nano** | Tegra | 0.5 TOPS | 教育/DIY |

### 5. DRIVE 汽车平台

| 平台 | 芯片 | 算力 | 级别 |
|------|------|------|------|
| **DRIVE Thor** | Thor | 2000 TOPS | L4 自动驾驶 |
| **DRIVE Orin** | Orin | 254 TOPS | L2+/L3 |
| **DRIVE AGX** | Orin/Xavier | 可变 | 开发平台 |
| **DRIVE Hyperion** | 传感器套件 | - | 参考设计 |

### 6. 网络产品

| 类别 | 产品 | 特点 |
|------|------|------|
| **DPU** | BlueField-4 | 800Gb/s, AI 加速 |
| | BlueField-3 | 400Gb/s |
| **InfiniBand** | ConnectX-8 | 800Gb/s |
| | Quantum-2 | 64 端口交换机 |
| **Ethernet** | Spectrum-X | AI 优化以太网 |
| | SuperNIC | 低延迟网卡 |

### 7. Grace CPU

| 产品 | 配置 | 用途 |
|------|------|------|
| **Grace Hopper** | Grace + H100 | AI 超级芯片 |
| **Grace Blackwell** | Grace + B200 | 下一代超级芯片 |
| **Grace CPU** | 72 核 Arm | HPC/云计算 |

## 硬件系统架构图

```mermaid
flowchart TB
    subgraph Compute[计算]
        GPU[GPU]
        CPU[Grace CPU]
        DPU[BlueField DPU]
    end
    
    subgraph Memory[内存]
        HBM[HBM3/HBM3e]
        GDDR[GDDR6/GDDR7]
        DDR[DDR5]
    end
    
    subgraph Interconnect[互连]
        NVLink[NVLink]
        NVSwitch[NVSwitch]
        PCIe[PCIe 5.0]
        IB[InfiniBand]
    end
    
    subgraph Systems[系统]
        DGX_Sys[DGX]
        HGX_Sys[HGX]
        OVX[OVX]
    end
    
    GPU --> HBM
    GPU --> GDDR
    CPU --> DDR
    
    GPU --> NVLink
    NVLink --> NVSwitch
    GPU --> PCIe
    DPU --> IB
    
    Compute --> Systems
    Memory --> Systems
    Interconnect --> Systems
```

## 产品发现统计

| 硬件类别 | 发现数量 |
|----------|----------|
| 消费级 GPU | 383 款 |
| 专业级 GPU | 45 款 |
| 数据中心 GPU | 32 款 |
| 汽车平台 | 19 款 |
| Jetson 嵌入式 | 24 款 |
| 网络产品 | 38 款 |
| DGX 系统 | 12 款 |
| **总计** | **562 款** |

---

*此树状图基于 NVIDIA 官网 10,000 页面爬取分析生成*
