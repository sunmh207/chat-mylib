CREATE DATABASE mylib;

USE mylib;

CREATE TABLE `resource` (
  `id` varchar(40) NOT NULL,
  `name` varchar(255) NOT NULL,
  `summary` text,
  `type` enum('txt','pdf','word','excel') DEFAULT 'txt',
  `created_time` int(11) DEFAULT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_time` int(11) DEFAULT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;