# NVIDIA Ecosystem Diagrams / NVIDIA 生态系统图表

> Generated: 2026-04-27 12:43:10

## Ecosystem Overview / 生态系统概览

```mermaid
mindmap
  root((NVIDIA Ecosystem))
    Hardware Ecosystem
      Geforce
      Networking
      Products
      Design Visualization
      Autonomous Machines
    Software Ecosystem
      Omniverse
      Clara
      Cuda
      Ai Data Science
      Data Center
    Developer Ecosystem
      Docs
      Ai Data Science
      Nvidia
      Downloads
      Ngc
    Business Ecosystem
      Industries
      Solutions
      Self Driving Cars
      Deep Learning Ai
      Design Visualization
    Technology Ecosystem
      Data Center
      Ai
      Launchpad
      Topics
      Solutions
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
    "Hardware Ecosystem" : 4732
    "Software Ecosystem" : 812
    "Developer Ecosystem" : 1017
    "Business Ecosystem" : 1836
    "Technology Ecosystem" : 1603
```

## Product Hierarchy / 产品层级

```mermaid
mindmap
  root((NVIDIA Products))
    Automotive
      DRIVE AGX
      DRIVE Hyperion
      DRIVE Orin
      DRIVE Sim
      DRIVE Thor
    Consumer GPU
      GEFORCE GTX 1050
      GEFORCE GTX 1050ti
      GEFORCE GTX 1060
      GEFORCE GTX 1070
      GEFORCE GTX 1070 Ti
      GEFORCE GTX 1080
      GEFORCE GTX 1080 Ti
      GEFORCE GTX 1650
    DGX Systems
      DGX Cloud
      DGX SUPERPOD
      DGX Station
    Data Center GPU
      A100
      B100
      DGX A100
      DGX H100
      H100
      L40
      L40S
      TESLA V100
    Data Center Platform
      Grace CPU
      Grace Hopper
    Edge AI / Embedded
      JETSON AGX Xavier
      Jetson AGX ORIN
      Jetson NANO
      Jetson Orin
      Jetson TX1
      Jetson TX2
      Jetson Xavier
    Networking
      BlueField
      BlueField-2
      BlueField-3
      BlueField-4
      ConnectX
      ConnectX-3
      ConnectX-4
      ConnectX-5
    Other Hardware
      B200
      H200
      L4
    Professional GPU
      Quadro 1200
      Quadro 2000
      Quadro 400
      Quadro 4000
      Quadro 410
      Quadro 5000
      Quadro 600
      Quadro 6000
```

## Technology Stack / 技术栈

```mermaid
mindmap
  root((NVIDIA Software))
    AI Frameworks
      Merlin
      Merlin Devzone Survey
      Merlin Distributed Embeddings
      Merlin Distributed Training
      Merlin Feature Engineering
      Merlin HugeCTR
      Merlin HugeCTR Core
      Merlin HugeCTR Framework
    AI Inference
      DeepStream Triton Server
      Isaac ROS TensorRT
      Morpheus Triton Models
      Morpheus Triton Server
      NGC TensorRT container
      TENSORRT
      TensorRT 10
      TensorRT 10.0
    CUDA Platform
      CUDA
      CUDA 10
      CUDA 10.0
      CUDA 10.1
      CUDA 10.2
      CUDA 101
      CUDA 11
      CUDA 11.0
    Cloud & Containers
      NGC
      NGC ACROSS PLATFORMS
      NGC AI
      NGC AI Enterprise
      NGC AI catalog
      NGC AI products
      NGC API
      NGC API Documentation
    Computer Vision
      DEEPSTREAM SDK
      DeepStream
      DeepStream 3D
      DeepStream 6
      DeepStream 7
      DeepStream 8
      DeepStream Alvin Clark
      DeepStream Composer
    Graphics Technology
      DLSS
      DLSS 1
      DLSS 2
      DLSS 3
      DLSS 4
      RAY TRACING
      REFLEX
    Healthcare AI
      CLARA
      CLARA AGX
      CLARA PARABRICKS DOCUMENTATION
      CLARA PARABRICKS PIPELINES
      CLARA SDK Pakiet
      CLARA Uniwersalna platforma
      Clara AGX AI
      Clara AGX Calcul
    Interconnect Technology
      NVLINK
      NVSWITCH
    Omniverse Platform
      NGC NVIDIA Omniverse
      NGC Omniverse Base
      NGC Omniverse Kit
      OMNIVERSE CONFERENCE SESSIONS
      OMNIVERSE CONNECTOR crashing
      OMNIVERSE ISAAC SIM
      OMNIVERSE LICENSING
      Omniverse
    Other Software
      Base Command
      Canvas
      Fleet Command
      NVIDIA AI Enterprise
      NVIDIA Enterprise
      TAO Toolkit
    Robotics
      ISAAC
      ISAAC Gym does
      ISAAC ROS Docker
      ISAAC ROS ESS
      ISAAC ROS vSLAM
      ISAAC ROS version
      ISAAC SIM
      ISAAC SIM URDF
    Speech & Audio AI
      BROADCAST
      Maxine
      Maxine 3D
      Maxine 4
      Maxine 50
      Maxine AI developer
      Maxine AR
      Maxine AR SDK
```
