# NVIDIA Ecosystem Diagrams / NVIDIA 生态系统图表

> Generated: 2026-04-24 16:01:11

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
      Merlin Devzone Survey Form
      Merlin Distributed Embeddings
      Merlin Explore the components of NVIDIA 
      Merlin Feature Engineering
      Merlin HugeCTR
      Merlin HugeCTR All
    AI Inference
      DeepStream SDK or TensorRT
      DeepStream and NVIDIA Triton
      DeepStream and NVIDIA Triton Inference S
      Deepstream and TensorRT
      Isaac ROS TensorRT Node with dynamic bat
      Morpheus Triton Server Models container
      Morpheus and Triton are located on the s
      NGC TensorRT container version
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
      NGC A portal of enterprise services
      NGC AI
      NGC AI Enterprise catalog at
      NGC AI catalog at
      NGC AI products through
      NGC AND GOOGLE CLOUD
      NGC AND GOOGLE CLOUD Chintan Patel
    Computer Vision
      DEEPSTREAM SDK
      DEEPSTREAM SDK FOR INTELLIGENT VIDEO ANA
      DeepStream
      DeepStream 3D
      DeepStream 6
      DeepStream 7
      DeepStream 8
      DeepStream Alvin Clark
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
      CLARA for HEALTHCARE
      Clara AGX AI
      Clara AGX KI
      Clara AGX dev kit Not detecting RTX6000 
    Interconnect Technology
      NVLINK
      NVSWITCH
    Omniverse Platform
      Isaac SIM in omniverse not launching
      Isaac Sim does not open from Omniverse G
      Isaac Sim into their software solutions 
      Isaac Sim without Omniverse Editor
      Isaac sim unity3d examples on isaac sim 
      Metropolis and NVIDIA Omniverse
      Metropolis e o NVIDIA Omniverse
      Metropolis y NVIDIA Omniverse
    Other Software
      Base Command
      Canvas
      Fleet Command
      NVIDIA AI Enterprise
      NVIDIA Enterprise
      TAO Toolkit
    Robotics
      ISAAC
      ISAAC Gym does not run in headless mode 
      ISAAC ROS Docker failed to inject CDI de
      ISAAC ROS ESS Stereo Depth Estimation no
      ISAAC ROS for Inference
      ISAAC ROS vSLAM questions on localizatio
      ISAAC ROS version for jetpack5
      ISAAC SIM
    Speech & Audio AI
      BROADCAST
      Maxine
      Maxine 3D
      Maxine 4
      Maxine 50
      Maxine AI developer platform
      Maxine AR
      Maxine AR SDK Audio2Face 2D Effect Maxin
```
