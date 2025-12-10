"""
Particle Swarm Optimization (PSO): Swarm intelligence optimization algorithm.

Uses swarm of particles to find optimal solutions through collective search.
"""

import numpy as np
from typing import Dict, List, Optional, Callable, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import logging

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Particle:
    """Represents a particle in PSO."""
    position: np.ndarray
    velocity: np.ndarray
    best_position: np.ndarray
    best_fitness: float = float('inf')
    fitness: float = float('inf')


class PSOOptimizer:
    """
    Particle Swarm Optimization for parameter optimization.
    
    Uses swarm of particles to search for optimal parameters.
    """
    
    def __init__(
        self,
        objective_function: Callable[[np.ndarray], float],
        bounds: List[Tuple[float, float]],  # [(min, max), ...] for each dimension
        num_particles: int = 30,
        w: float = 0.7,  # Inertia weight
        c1: float = 1.5,  # Cognitive coefficient
        c2: float = 1.5,  # Social coefficient
        max_iterations: int = 100
    ):
        """
        Initialize PSO optimizer.
        
        Args:
            objective_function: Function to minimize
            bounds: Bounds for each dimension
            num_particles: Number of particles in swarm
            w: Inertia weight
            c1: Cognitive coefficient (attraction to personal best)
            c2: Social coefficient (attraction to global best)
            max_iterations: Maximum iterations
        """
        self.objective_function = objective_function
        self.bounds = np.array(bounds)
        self.num_particles = num_particles
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.max_iterations = max_iterations
        
        self.dimensions = len(bounds)
        self.particles: List[Particle] = []
        self.global_best_position: Optional[np.ndarray] = None
        self.global_best_fitness = float('inf')
        
        self.logger = get_logger(__name__)
        self._initialize_swarm()
    
    def _initialize_swarm(self) -> None:
        """Initialize particle swarm."""
        self.particles = []
        
        for i in range(self.num_particles):
            # Random position within bounds
            position = np.array([
                np.random.uniform(min_val, max_val)
                for min_val, max_val in self.bounds
            ])
            
            # Random velocity (scaled by bounds)
            velocity_ranges = self.bounds[:, 1] - self.bounds[:, 0]
            velocity = np.random.uniform(-velocity_ranges, velocity_ranges) * 0.1
            
            particle = Particle(
                position=position,
                velocity=velocity,
                best_position=position.copy()
            )
            
            # Evaluate initial fitness
            particle.fitness = self.objective_function(position)
            particle.best_fitness = particle.fitness
            
            # Update global best
            if particle.fitness < self.global_best_fitness:
                self.global_best_fitness = particle.fitness
                self.global_best_position = position.copy()
            
            self.particles.append(particle)
    
    def optimize(self) -> Tuple[np.ndarray, float, List[Dict[str, Any]]]:
        """
        Run PSO optimization.
        
        Returns:
            (best_position, best_fitness, history) tuple
        """
        history = []
        
        for iteration in range(self.max_iterations):
            # Update each particle
            for particle in self.particles:
                # Update velocity
                r1 = np.random.rand(self.dimensions)
                r2 = np.random.rand(self.dimensions)
                
                cognitive = self.c1 * r1 * (particle.best_position - particle.position)
                social = self.c2 * r2 * (self.global_best_position - particle.position)
                
                particle.velocity = (
                    self.w * particle.velocity + cognitive + social
                )
                
                # Update position
                particle.position += particle.velocity
                
                # Apply bounds
                particle.position = np.clip(
                    particle.position,
                    self.bounds[:, 0],
                    self.bounds[:, 1]
                )
                
                # Evaluate fitness
                particle.fitness = self.objective_function(particle.position)
                
                # Update personal best
                if particle.fitness < particle.best_fitness:
                    particle.best_fitness = particle.fitness
                    particle.best_position = particle.position.copy()
                    
                    # Update global best
                    if particle.fitness < self.global_best_fitness:
                        self.global_best_fitness = particle.fitness
                        self.global_best_position = particle.position.copy()
            
            # Record history
            history.append({
                "iteration": iteration + 1,
                "best_fitness": self.global_best_fitness,
                "average_fitness": np.mean([p.fitness for p in self.particles]),
                "swarm_diversity": self._calculate_diversity()
            })
            
            if (iteration + 1) % 10 == 0:
                self.logger.info(f"PSO Iteration {iteration+1}/{self.max_iterations}: "
                               f"Best Fitness: {self.global_best_fitness:.4f}")
        
        return self.global_best_position, self.global_best_fitness, history
    
    def _calculate_diversity(self) -> float:
        """Calculate swarm diversity (average distance between particles)."""
        positions = np.array([p.position for p in self.particles])
        centroid = np.mean(positions, axis=0)
        distances = np.linalg.norm(positions - centroid, axis=1)
        return np.mean(distances)

