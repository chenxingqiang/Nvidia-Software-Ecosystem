# NVIDIA Ecosystem Diagrams / NVIDIA 生态系统图表

> Generated: 2026-04-17 01:19:34

## Ecosystem Overview / 生态系统概览

```mermaid
mindmap
  root((NVIDIA Ecosystem))
    Hardware Ecosystem
      Geforce
      Data Center
      Networking
      Autonomous Machines
      Self Driving Cars
    Software Ecosystem
      Autonomous Machines
      Deep Learning Ai
      Cudnn
      Omniverse
      Data Center
    Developer Ecosystem
      Cuda Toolkit
      Triton Inference Server
      Maxine
      Riva
      Nsight Systems
    Business Ecosystem
      Deep Learning Ai
      Solutions
      Industries
    Technology Ecosystem
      Data Center
      Deep Learning Ai
      High Performance Computing
      Tensorrt
      Ai Data Science
```

## Ecosystem Relationships / 生态系统关系

```mermaid
flowchart TD
    NVIDIA["NVIDIA Platform"]
    hardware["Hardware Ecosystem"]
    NVIDIA --> hardware
    software["Software Ecosystem"]
    NVIDIA --> software
    developer["Developer Ecosystem"]
    NVIDIA --> developer
    business["Business Ecosystem"]
    NVIDIA --> business
    technology["Technology Ecosystem"]
    NVIDIA --> technology
    hardware -.->|"powers"| software
    software -.->|"enables"| developer
    developer -.->|"implements"| technology
    technology -.->|"drives"| business
    hardware -.->|"accelerates"| technology
```

## Distribution / 分布

```mermaid
pie title "NVIDIA Ecosystem Distribution"
    "Hardware Ecosystem" : 24
    "Software Ecosystem" : 9
    "Developer Ecosystem" : 8
    "Business Ecosystem" : 3
    "Technology Ecosystem" : 15
```

## Product Hierarchy / 产品层级

```mermaid
mindmap
  root((NVIDIA Products))
    Automotive
      DRIVE Thor
      DRIVE Sim
      DRIVE Hyperion
      DRIVE AGX
    Consumer GPU
      RTX 6000
      GeForce RTX 40
      GeForce RTX 5070 Ti
      RTX 5000
      RTX 4500
      RTX 5080
      GeForce RTX 4090
      RTX 4000
    DGX Systems
      DGX Cloud
      DGX SuperPOD
      DGX Station
    Data Center GPU
      DGX H100
      H100
      L40
      A100
      DGX A100
    Data Center Platform
      Grace Hopper
      Grace CPU
    Edge AI / Embedded
      Jetson AGX Xavier
      Jetson Orin
      Jetson AGX Orin
    Networking
      Spectrum-4
      ConnectX-7
      BlueField
      BlueField-3
    Other Hardware
      H200
```

## Technology Stack / 技术栈

```mermaid
mindmap
  root((NVIDIA Software))
    AI Frameworks
      NeMo large
      RAPIDS
      Merlin is
      RAPIDS container
      NeMo is
      Morpheus AI
      Merlin
      NeMo Curator
    AI Inference
      Triton Inference Server
      TensorRT
      TensorRT 10
    CUDA Platform
      CUDA
      cuDNN 9
      cuDNN
    Cloud & Containers
      NGC catalog
      NGC
      NGC Catalog
      NGC is
    Computer Vision
      Metropolis
      DeepStream for
      DeepStream
      DeepStream video
      Metropolis platform
      DeepStream SDK
    Graphics Technology
      Ray Tracing
      DLSS
      DLSS 4
      Ray tracing
      DLSS 3
      ray tracing
      Reflex
    Healthcare AI
      Clara healthcare
      Clara Discovery
      Clara
      Clara Imaging
      Clara Holoscan
      Clara is
    Interconnect Technology
      NVSwitch
      NVLink
    Omniverse Platform
      Omniverse platform
      Omniverse is
      Omniverse Platform
      Omniverse Enterprise
      Omniverse Cloud
      Omniverse for
      Omniverse 3D協作平台
      Omniverse 3D协作平台
    Other Software
      Canvas
      NVIDIA enterprise
      TAO Toolkit
      NVIDIA AI Enterprise
      Base Command
    Robotics
      Isaac
      Isaac Lab
      Isaac SDK
      Isaac Manipulator
      Isaac for
      Isaac 平台
      Isaac 机器人平台
      Isaac Sim
    Speech & Audio AI
      Maxine SDK
      Maxine
      Broadcast
      Riva speech
      riva
      Riva
      Riva is
```
