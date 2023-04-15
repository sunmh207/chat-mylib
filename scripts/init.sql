CREATE DATABASE IF NOT EXISTS mylib;

USE mylib;

CREATE TABLE IF NOT EXISTS `resource` (
    `id` VARCHAR(40) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `summary` TEXT,
    `type` ENUM('txt', 'pdf', 'word', 'excel') DEFAULT 'txt',
    `created_time` INT(11) DEFAULT NULL,
    `updated_time` INT(11) DEFAULT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;