

CREATE TABLE `vcf_genotypes` (
  `genome` VARCHAR(6) NOT NULL,
  `contig` VARCHAR(2) NOT NULL,
  `sample` VARCHAR(50) NOT NULL,
  `pos` INT(9) NOT NULL,
  `ref` VARCHAR(1000) NOT NULL,
  `alt` VARCHAR(1000) NOT NULL,
  `zigosity` VARCHAR(3) NOT NULL,
  `genotype_details` VARCHAR(5000) NOT NULL,
  PRIMARY KEY (`genome`,`contig`,`sample`,`pos`),
  KEY `by_genome` (`genome`),
  KEY `by_contig` (`contig`),
  KEY `by_pos` (`pos`),
  KEY `by_ref` (`ref`(10)),
  KEY `by_alt` (`alt`(10))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `available_genomes` (
  `genome` VARCHAR(6) NOT NULL,
  PRIMARY KEY (`genome`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

