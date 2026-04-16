# NVIDIA Ecosystem Diagrams / NVIDIA 生态系统图表

> Generated: 2026-04-16 03:32:11

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
      Ai
      Deep Learning Ai
      High Performance Computing
      Tensorrt
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
    "Technology Ecosystem" : 16
```

## Product Hierarchy / 产品层级

```mermaid
mindmap
  root((NVIDIA Products))
    Automotive
      DRIVE Thor
      DRIVE Sim
      DRIVE AGX
      DRIVE Hyperion
    Consumer GPU
      RTX 4090
      RTX 4070 Ti
      GeForce RTX 40
      RTX 4500
      RTX 5070
      RTX 4000
      GeForce RTX 4080
      RTX 5080
    DGX Systems
      DGX Cloud
      DGX Station
      DGX SuperPOD
    Data Center GPU
      H100
      DGX H100
      L40
      DGX A100
      A100
    Data Center Platform
      Grace Hopper
      Grace CPU
    Edge AI / Embedded
      Jetson AGX Xavier
      Jetson Orin
      Jetson AGX Orin
    Networking
      BlueField-3
      Spectrum-4
      BlueField
      ConnectX-7
    Other Hardware
      H200
```

## Technology Stack / 技术栈

```mermaid
mindmap
  root((NVIDIA Software))
    AI Frameworks
      NeMo is
      RAPIDS container
      NeMo framework
      NeMo Retriever
      Morpheus
      NeMo large
      Merlin recommender
      RAPIDS suite
    AI Inference
      TensorRT 10
      TensorRT
      Triton Inference Server
    CUDA Platform
      CUDA
      cuDNN
      cuDNN 9
    Cloud & Containers
      NGC Catalog
      NGC catalog
      NGC
      NGC is
    Computer Vision
      Metropolis
      DeepStream SDK
      DeepStream video
      Metropolis platform
      DeepStream for
      DeepStream
    Graphics Technology
      DLSS 3
      Reflex
      ray tracing
      Ray Tracing
      DLSS 4
      Ray tracing
      DLSS
    Healthcare AI
      Clara
      Clara healthcare
      Clara Holoscan
      Clara Imaging
      Clara Discovery
      Clara is
    Interconnect Technology
      NVLink
      NVSwitch
    Omniverse Platform
      Omniverse platform
      Omniverse is
      Omniverse 3D協作平台
      Omniverse Platform
      Omniverse Cloud
      Omniverse Enterprise
      Omniverse for
      Omniverse 3D协作平台
    Other Software
      Base Command
      NVIDIA enterprise
      TAO Toolkit
      NVIDIA AI Enterprise
      Canvas
    Robotics
      Isaac robotics
      Isaac 机器人平台
      Isaac 平台
      Isaac Perceptor
      Isaac SDK
      Isaac Sim
      Isaac ROS
      Isaac
    Speech & Audio AI
      Riva is
      riva
      Maxine SDK
      Maxine
      Broadcast
      Riva
      Riva speech
```
