CREATE TABLE `users` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  `username` text UNIQUE NOT NULL,
  `credits` integer DEFAULT 0,
  `created_at` integer
);

CREATE TABLE `cases` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  `name` text,
  `price_cents` integer
);

CREATE TABLE `loot_items` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  `case_id` integer,
  `key_name` text,
  `display_name` text,
  `weight` integer,
  `payload` text
);

CREATE TABLE `case_openings` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  `user_id` integer,
  `case_id` integer,
  `loot_item_id` integer,
  `outcome` text,
  `created_at` integer
);

ALTER TABLE `loot_items` ADD FOREIGN KEY (`case_id`) REFERENCES `cases` (`id`);

ALTER TABLE `case_openings` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `case_openings` ADD FOREIGN KEY (`case_id`) REFERENCES `cases` (`id`);

ALTER TABLE `case_openings` ADD FOREIGN KEY (`loot_item_id`) REFERENCES `loot_items` (`id`);
