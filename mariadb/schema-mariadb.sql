

CREATE TABLE `vcf_genotypes` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `genome` VARCHAR(6) NOT NULL,
  `contig` VARCHAR(2) NOT NULL,
  `sample` VARCHAR(50) NOT NULL,
  `pos` INT(9) NOT NULL,
  `ref` VARCHAR(1000) NOT NULL,
  `alt` VARCHAR(1000) NOT NULL,
  `zigosity` VARCHAR(3) NOT NULL,
  `genotype_details` VARCHAR(5000) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `by_genome` (`genome`),
  KEY `by_contig` (`contig`),
  KEY `by_sample` (`sample`),
  KEY `by_pos` (`pos`),
  KEY `by_ref` (`ref`(10)),
  KEY `by_alt` (`alt`(10))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `vcf_samples` (
  `genome` VARCHAR(6) NOT NULL,
  `sample` VARCHAR(50) NOT NULL,
  `sample_details` VARCHAR(5000),
  PRIMARY KEY (`genome`,`sample`),
  KEY `by_genome` (`genome`),
  KEY `by_sample` (`sample`),
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `available_genomes` (
  `genome` VARCHAR(6) NOT NULL,
  PRIMARY KEY (`genome`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

